"""Hyperparameter evaluation harness for the RAG retriever.

Scientifically determines the best chunk size k (and overlap, and retrieval
depth n_results) instead of guessing them. Method:

  1. Gold set      -- a fixed list of (query -> the policy passage that SHOULD
                      be retrieved). Hand-labelled once, below.
  2. Sweep         -- for each (chunk_size, overlap) config, re-chunk + re-embed
                      the policies into a throwaway in-memory collection.
  3. Score         -- for each gold query, retrieve top-n and check whether a
                      retrieved chunk actually contains the target passage.
                      Metrics: hit-rate (fraction found) and MRR (mean
                      reciprocal rank -- rewards finding it higher up).
  4. Rank          -- print a table sorted best-first and recommend a config.

Run:  python eval_chunks.py

It touches NO persistent state (own in-memory collections), so it never
disturbs the app's chroma_db.
"""

import re
import sys

from langchain_chroma import Chroma
from langchain_core.documents import Document

from indexer import chunk_text, embedder

# --- 1. Gold set: query -> (expected source file, distinctive target phrase) ---
# The target phrase is a short, unique snippet that lives in exactly one place in
# the policies. Retrieval "hits" only if a returned chunk contains that phrase --
# so a chunking that splits the phrase across a boundary (or buries it in noise)
# is correctly scored as a miss.
GOLD = [
    ("staff disciplinary outcomes broken down by job grade",
     "fewer than 5 individuals"),
    ("can we release tender evaluation scores for unsuccessful bidders",
     "ranking of unsuccessful bidders"),
    ("which exemption protects third party personal data",
     "most frequently applied exemption"),
    ("commercial interests exemption for contract pricing",
     "tender pricing, contract negotiation details"),
    ("what is the cost limit for complying with a request",
     "18 hours of staff time"),
    ("how long do we have to respond to an FOI request",
     "20 working days"),
    ("how should redactions be applied to documents",
     "solid black redaction bars"),
    ("internal emails and meeting notes about a policy decision",
     "internal policy deliberations may be protected under Section 36"),
    ("aggregate headcount by grade release",
     "Aggregate statistics"),
    ("public interest test factors favouring disclosure",
     "transparency, accountability, and public understanding"),
]

POLICIES_DIR = "documents/policies"


def _norm(s: str) -> str:
    """Collapse whitespace + lowercase so phrase matching is robust to wrapping."""
    return re.sub(r"\s+", " ", s).strip().lower()


def _policy_docs(chunk_size: int, overlap: int):
    from pathlib import Path

    docs = []
    for path in sorted(Path(POLICIES_DIR).glob("*.txt")):
        for i, chunk in enumerate(chunk_text(path.read_text(), chunk_size, overlap)):
            docs.append(Document(page_content=chunk, metadata={"file": path.name}))
    return docs


def evaluate(chunk_size: int, overlap: int, n_results: int, tag: str) -> dict:
    """Index one config into a throwaway collection and score it against GOLD."""
    docs = _policy_docs(chunk_size, overlap)
    store = Chroma(collection_name=f"eval_{tag}", embedding_function=embedder)
    store.add_documents(docs)

    hits, rr = 0, 0.0
    for query, target in GOLD:
        results = store.similarity_search(query, k=n_results)
        tnorm = _norm(target)
        rank = next(
            (i + 1 for i, d in enumerate(results) if tnorm in _norm(d.page_content)),
            None,
        )
        if rank:
            hits += 1
            rr += 1 / rank

    store.delete_collection()
    n = len(GOLD)
    return {
        "chunk_size": chunk_size,
        "overlap": overlap,
        "n_results": n_results,
        "chunks": len(docs),
        "hit_rate": hits / n,
        "mrr": rr / n,
    }


def main():
    # Grid: vary chunk_size x overlap at a fixed retrieval depth, then re-check
    # retrieval depth at the winning chunk config.
    chunk_sizes = [200, 300, 400, 500, 600, 800]
    overlaps = [0, 80, 160]
    base_n = 3

    rows = []
    tag = 0
    print(f"Sweeping {len(chunk_sizes) * len(overlaps)} configs "
          f"(n_results={base_n}) over {len(GOLD)} gold queries...\n")
    for cs in chunk_sizes:
        for ov in overlaps:
            if ov >= cs:
                continue  # overlap must be smaller than the chunk
            tag += 1
            rows.append(evaluate(cs, ov, base_n, str(tag)))

    rows.sort(key=lambda r: (r["hit_rate"], r["mrr"]), reverse=True)

    print(f"{'chunk':>6} {'overlap':>7} {'n':>3} {'chunks':>6} "
          f"{'hit_rate':>8} {'MRR':>6}")
    print("-" * 44)
    for r in rows:
        print(f"{r['chunk_size']:>6} {r['overlap']:>7} {r['n_results']:>3} "
              f"{r['chunks']:>6} {r['hit_rate']:>8.2f} {r['mrr']:>6.3f}")

    best = rows[0]
    print(f"\nBest chunk config: chunk_size={best['chunk_size']}, "
          f"overlap={best['overlap']} "
          f"(hit_rate={best['hit_rate']:.2f}, MRR={best['mrr']:.3f})")

    # Now sweep retrieval depth at the winning chunk config.
    print(f"\nRetrieval-depth sweep at chunk_size={best['chunk_size']}, "
          f"overlap={best['overlap']}:")
    print(f"{'n_results':>9} {'hit_rate':>8} {'MRR':>6}")
    print("-" * 25)
    for n in (1, 2, 3, 5):
        tag += 1
        r = evaluate(best["chunk_size"], best["overlap"], n, str(tag))
        print(f"{n:>9} {r['hit_rate']:>8.2f} {r['mrr']:>6.3f}")

    print("\nApply the winner by updating the defaults in indexer.chunk_text "
          "and the n_results in search_policies.")


if __name__ == "__main__":
    sys.exit(main())
