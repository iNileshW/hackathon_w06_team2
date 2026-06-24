# AI Assistance Log

Record every instance where you use AI to generate, refactor, or debug code. Four fields per entry: what you asked for, what the AI produced, what you changed, and why you changed it.

## Instance 1: Triage agent classification prompt

| Field | Detail |
|-------|--------|
| **Date** | YYYY-MM-DD |
| **Task** | Scaffolded the triage agent's classification prompt for FOI request categorisation |
| **What AI Generated** | System prompt with 5 topic categories (personal-data, environmental, financial, operational, policy). Classification output as free-text paragraph. Did not include complexity rating. Used ambiguous phrasing ("try to classify") rather than a structured output format. |
| **What You Changed + Why** | Changed output format from free-text to JSON (`{"topic": "...", "complexity": "high|medium|low"}`) -- structured output is required by the supervisor for downstream routing. Added complexity field (high/medium/low) -- compliance agent needs this to decide retrieval depth. Changed "try to classify" to "classify the following request" -- hedging language produces unreliable output. Added a fallback category ("other") -- requests that do not fit the five categories should not crash the pipeline. |

## Instance 2: Multi-agent pipeline + supervisor (Req 1)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Implement Requirement 1 -- three distinct agents (triage, compliance, response) orchestrated by a supervisor, replacing the stubbed function bodies in `agents.py`. |
| **What AI Generated** | Full bodies for `triage_agent`, `compliance_agent`, `response_agent`, and the `supervisor`. Triage sends the request to Claude (`claude-sonnet-4-5`) and parses a JSON `{topic, complexity, summary}` against a fixed topic set. Compliance calls `search_policies()`, injects the excerpts into the prompt, and returns `{exemptions_found, reasoning, policy_sources, recommendation}`. Response drafts a formal letter from the triage + compliance outputs. Supervisor runs the three in sequence. Also added a `_parse_json` helper to strip ```` ```json ```` fences. |
| **What You Changed + Why** | Wrapped **each** supervisor stage in its own try/except with a documented fallback (not just the agents' internal handling) -- the brief requires one failing request not to crash the batch, so the orchestrator needs its own safety net. Constrained triage to a fixed topic list and instructed "JSON only, no prose" -- free-text classification is unreliable for downstream routing. Told the compliance agent to use ONLY the supplied policy excerpts -- prevents the model inventing law not in the documents. Defaulted compliance fallback to `recommendation="withhold"` -- fail safe (don't release on error). Left RAG retrieval (Req 2), the approval gate (Req 3), cost math (Req 5), and the JSON cost field (Req 6) stubbed -- scoped strictly to Req 1. |

## Instance 3: Testing the Req 1 pipeline flow

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Verify the Req 1 multi-agent pipeline runs end to end -- confirm triage, compliance, and response all execute in order and the supervisor returns a populated result dict. |
| **What AI Generated** | A no-key structural test: a `FakeClient` whose `.invoke()` returns canned JSON, passed to `supervisor()`, asserting the result dict contains `classification`, `compliance`, `draft_response`, and `human_decision`. Then a real run -- `python main.py index` followed by `python main.py process documents/foi_requests/request-001.txt` -- against the live Anthropic API once the key was added to `.env`. |
| **What You Changed + Why** | Ran the mock test first before spending API tokens -- it isolates orchestration wiring from LLM behaviour, so a green mock means a red real run points at the API/key, not the supervisor. Confirmed the real run logged 3 LLM calls with no `[agent] error, using fallback` lines -- that absence is the actual pass signal, since the try/except fallbacks would otherwise hide a broken agent behind a populated-looking dict. Noted three expected non-failures and did NOT treat them as Req 1 bugs: `policy_sources: []` (indexer stub, Req 2), `$0.0000` cost (cost-calc stub, Req 5), and auto-approved checkpoint (HITL stub, Req 3) -- all out of Req 1 scope. |

## Instance 4: RAG over ChromaDB -- compliance retrieval (Req 2)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Implement Requirement 2 -- fill the stubbed `index_policies` and `search_policies` in `indexer.py` so the compliance agent retrieves real policy excerpts from ChromaDB and cites their source filenames. |
| **What AI Generated** | `index_policies`: wipes any existing collection (try/except), then reads each `.txt` in the policies dir, splits it with the existing `chunk_text` (400/80), wraps each chunk as a `Document` with metadata `{"file", "chunk_index"}` and id `f"{filename}-{i}"`, and bulk-loads via `add_documents`; returns the chunk count. `search_policies`: `similarity_search(query, k=3)` wrapped in try/except, returning `[{"text", "source"}]` (source from `metadata["file"]`) or `[]` on failure. The compliance agent was already wired to consume these from the Req 1 commit, so no `agents.py` change was needed. |
| **What You Changed + Why** | The first run reported "20 chunks" but compliance still got `policy_sources: []`. Root cause: `Chroma()` had no `persist_directory`, so the store lived in RAM -- and `index` and `process` are two separate `python` invocations, so the indexed data died when the index process exited. Added `persist_directory=chroma_db/` to BOTH `Chroma()` constructors (module-level and the re-index reassignment) so the store survives on disk and is shared across runs -- the bug type that passes in one script but fails in the real two-command CLI flow, which is why I tested `index` and `process` as separate commands instead of one. Wrapped `search_policies` retrieval in try/except returning `[]` -- reuses the Req 4 fail-safe pattern so a vector-store error degrades compliance instead of crashing it. Added `chroma_db/` to `.gitignore` since the store is generated. |

## Instance 5: Human-in-the-loop approval gate (Req 3)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Implement Requirement 3 -- replace the auto-approving `human_checkpoint` stub in `agents.py` with a real approve/reject/modify gate that pauses execution, shows the operator the evidence, and writes a timestamped decision-log entry. |
| **What AI Generated** | A `human_checkpoint` that prints the draft letter, evidence summary, and policy citations; prompts via a `_read_decision` helper accepting `approve/reject/modify` (and `a/r/m`); collects required notes on modify and an optional reason on reject; builds a record `{timestamp (UTC ISO 8601), request_id, decision, notes, evidence_refs}`; and appends it as one JSON line to `decisions.log` (opened in `"a"` mode). Added a `_read_decision` validation loop and wired the supervisor to pass `compliance["policy_sources"]` as `evidence_refs`. |
| **What You Changed + Why** | Made the gate fail safe to `reject` on `EOFError` (no input stream) instead of letting `input()` crash -- the brief says nothing is released without approval, so an absent operator must NOT default to approve. Added an `evidence_refs` parameter and fed it the compliance policy sources so the audit log records WHAT evidence backed each decision, not just the verdict -- a decision log without its evidence is not auditable. Wrote the log as JSONL appended next to the module (path derived from `__file__`, not CWD) so the audit trail accumulates across runs and is found regardless of where the CLI is launched. Returned the full record dict (not just `{decision, notes}`) so Req 6's structured output already carries the timestamp and evidence refs. Tested all four paths -- approve, modify+notes, reject+reason, and EOF fail-safe -- by piping stdin, and gitignored `decisions.log` as a generated runtime artifact. |

## Instance 6: Error handling + fallback hardening (Req 4)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Implement Requirement 4 -- guarantee that an agent failure (API error, unparseable response, empty result) is logged and falls back rather than crashing, and that one bad request never aborts the batch. |
| **What AI Generated** | A `_content_or_raise(response)` helper that raises `ValueError` on empty/None content, called in all three agents so an empty result funnels into the same try/except that already catches API and JSON-parse errors. Wrapped the `supervisor()` call in `main.py`'s file loop in its own try/except, writing an `{request_file, error}` result and continuing to the next file on any crash. The per-agent try/except, documented fallbacks, and `_parse_json` JSON guard already existed from the Req 1 build. |
| **What You Changed + Why** | The big gap was the *empty/None* case the brief calls out: `response_agent` returned `response.content` blind, so an empty draft would have silently passed the gate as a valid response -- worse than a crash. Routed it through `_content_or_raise` so emptiness is treated as failure and yields the documented `[draft unavailable]` fallback. Added the `main.py` batch guard as a last-resort net BELOW the supervisor's per-stage handling -- defence in depth: even if the orchestrator itself (not an agent) throws, the remaining requests still process. Kept the broad `except Exception` rather than narrowing to `JSONDecodeError` -- the requirement lists three distinct failure classes (API/parse/empty) and one catch-all that logs the specific exception message covers all three without missing a fourth. Verified all six failure modes with mock clients (raise / empty / garbage JSON across triage, compliance, response, plus an all-fail supervisor run) and confirmed the real pipeline still passes unchanged. Noted that the compliance fallback now keeps the real `policy_sources` when RAG succeeded but the LLM failed -- richer than the spec's empty list and still safe. |
