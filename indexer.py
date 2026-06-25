"""Document indexing and retrieval using ChromaDB.

Indexes policy documents into a ChromaDB collection for RAG retrieval, via
LangChain's Chroma vector store wrapper.
"""

import hashlib
import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

COLLECTION_NAME = "foi_policies"
# Persist on disk so `index` and `process` (separate processes) share the store.
PERSIST_DIR = str(Path(__file__).resolve().parent / "chroma_db")
# Tracks the content hash + chunk count of each indexed file so sync_index can
# tell new / changed / deleted documents apart without re-embedding everything.
MANIFEST_PATH = Path(__file__).resolve().parent / ".index_manifest.json"

embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedder,
    persist_directory=PERSIST_DIR,
)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list:
    """Split text into overlapping chunks.

    Args:
        text: The full document text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def index_policies(policies_dir: str) -> int:
    """Index all .txt files in the policies directory into ChromaDB.

    Args:
        policies_dir: Path to the directory containing policy text files.

    Returns:
        The number of chunks indexed.

    """
    global vectorstore
    # Start from a clean collection so re-indexing never double-counts chunks.
    try:
        vectorstore.delete_collection()
    except Exception as exc:
        print(f"  [index] no existing collection to clear: {exc}")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedder,
        persist_directory=PERSIST_DIR,
    )

    documents = []
    ids = []
    for path in sorted(Path(policies_dir).glob("*.txt")):
        filename = path.name
        for i, chunk in enumerate(chunk_text(path.read_text())):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={"file": filename, "chunk_index": i},
                )
            )
            ids.append(f"{filename}-{i}")

    if documents:
        vectorstore.add_documents(documents, ids=ids)

    # Seed the manifest so a later sync_index() sees these files as up to date.
    _save_manifest({
        path.name: {"hash": _file_hash(path.read_text()),
                    "chunks": len(chunk_text(path.read_text()))}
        for path in sorted(Path(policies_dir).glob("*.txt"))
    })
    return len(documents)


def _file_hash(text: str) -> str:
    """Content hash used to detect whether a document changed."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_manifest() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def _ids_for(filename: str, count: int) -> list:
    return [f"{filename}-{i}" for i in range(count)]


def _upsert_file(path: Path, prev_chunks: int) -> int:
    """Re-index one file: drop its old chunks, add the current ones. Idempotent."""
    filename = path.name
    text = path.read_text()
    chunks = chunk_text(text)

    # Delete the file's previous chunks (covers the case where it now has fewer).
    old_ids = _ids_for(filename, max(prev_chunks, len(chunks)))
    if old_ids:
        try:
            vectorstore.delete(ids=old_ids)
        except Exception as exc:
            print(f"  [sync] delete of old chunks for {filename} failed: {exc}")

    docs = [
        Document(page_content=c, metadata={"file": filename, "chunk_index": i})
        for i, c in enumerate(chunks)
    ]
    if docs:
        vectorstore.add_documents(docs, ids=_ids_for(filename, len(chunks)))
    return len(chunks)


def sync_index(policies_dir: str) -> dict:
    """Incrementally bring the vector store in line with the policies folder.

    Unlike index_policies (which wipes and rebuilds everything), this only
    touches what changed -- so it scales to large, frequently-updated corpora:

    - new file      -> chunk + add
    - changed file  -> re-chunk + upsert (content hash differs)
    - unchanged     -> skip (no re-embedding)
    - deleted file  -> remove its chunks from the store

    Stable per-file ids (`{filename}-{i}`) make every operation idempotent, so
    this is safe to run on a timer, a file-watch event, or an upload webhook.

    Returns a summary dict: {added, updated, unchanged, removed, total_chunks}.
    """
    manifest = _load_manifest()
    current = {p.name: p for p in sorted(Path(policies_dir).glob("*.txt"))}

    added = updated = unchanged = removed = 0

    # New + changed + unchanged.
    for filename, path in current.items():
        text = path.read_text()
        h = _file_hash(text)
        entry = manifest.get(filename)
        if entry is None:
            n = _upsert_file(path, 0)
            manifest[filename] = {"hash": h, "chunks": n}
            added += 1
        elif entry["hash"] != h:
            n = _upsert_file(path, entry["chunks"])
            manifest[filename] = {"hash": h, "chunks": n}
            updated += 1
        else:
            unchanged += 1

    # Deleted: in the manifest but no longer on disk.
    for filename in [f for f in manifest if f not in current]:
        old_ids = _ids_for(filename, manifest[filename]["chunks"])
        try:
            vectorstore.delete(ids=old_ids)
        except Exception as exc:
            print(f"  [sync] delete of removed file {filename} failed: {exc}")
        del manifest[filename]
        removed += 1

    _save_manifest(manifest)
    total_chunks = sum(e["chunks"] for e in manifest.values())
    return {
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "removed": removed,
        "total_chunks": total_chunks,
    }


def watch_and_sync(policies_dir: str, interval: float = 5.0) -> None:
    """Poll the folder and sync on any change -- a simple automatic trigger.

    A dependency-free stand-in for a file-watch / upload-webhook trigger: in
    production you'd drive sync_index() from a watchdog observer, a cron job, or
    an object-storage event instead of a sleep loop.
    """
    import time

    print(f"Watching {policies_dir} every {interval}s for changes (Ctrl+C to stop)...")
    while True:
        summary = sync_index(policies_dir)
        if summary["added"] or summary["updated"] or summary["removed"]:
            print(f"  change detected -> {summary}")
        time.sleep(interval)


def search_policies(query: str, n_results: int = 3) -> list:
    """Search the policy collection for chunks relevant to the query.

    Args:
        query: The search query text.
        n_results: Number of results to return.

    Returns:
        A list of dictionaries with keys "text" and "source".
        Returns an empty list if the collection has no results.

    """
    try:
        docs = vectorstore.similarity_search(query, k=n_results)
    except Exception as exc:
        print(f"  [search] retrieval failed: {exc}")
        return []
    return [
        {"text": doc.page_content, "source": doc.metadata.get("file", "unknown")}
        for doc in docs
    ]
