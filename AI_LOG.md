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

## Instance 7: Cost tracking calculation (Req 5)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Implement Requirement 5 -- finish the stubbed cost calculation in `cost_tracker.py` so every LLM call records an estimated USD cost and the end-of-run summary prints model, tokens, and cost. |
| **What AI Generated** | Filled the `estimated_cost` calc in `log_call`: look up the model in `MODEL_COSTS`, default to `{"input": 0.0, "output": 0.0}` if absent, then `cost = input_tokens/1000 * input_rate + output_tokens/1000 * output_rate`. Also threaded the model name into the per-agent `summary()` breakdown and the `print_summary()` line. The `summary()` aggregation, `print_summary()` skeleton, and the agents' `log_call(...)` calls already existed from earlier reqs. |
| **What You Changed + Why** | Added the model name to each per-agent summary line (it was tracked per call but not surfaced) -- Req 5 explicitly requires logging "the model used", and the reference transcript prints model per agent, so the floor isn't met by tokens+cost alone. Used `MODEL_COSTS.get(model, zero-rates)` rather than raising on an unknown model -- an unpriced model should still be logged with its tokens (cost 0.0) instead of crashing the tracker, consistent with the Req 4 never-crash principle. Verified the arithmetic directly with a unit check (1k input + 1k output on sonnet = $0.018; unknown model = $0.0) and against a real run (3 calls, $0.0159 total, per-agent model + token + cost lines) -- the earlier `$0.0000` was the hardcoded stub, now replaced. |

## Instance 8: Per-request cost in structured output (Req 6)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Implement Requirement 6 -- ensure each request's JSON result carries all five field groups plus a `cost_breakdown`, the one field the supervisor's return dict was still omitting. |
| **What AI Generated** | Snapshot `cost_start = len(cost_tracker.calls)` at the top of `supervisor()`, then after the pipeline slice `cost_tracker.calls[cost_start:]` and assemble `cost_breakdown = {calls, total_tokens, total_cost_usd}`, added to the returned dict alongside `request_file`, `classification`, `compliance`, `draft_response`, and `human_decision`. The other five groups and `main.py`'s JSON writing already existed. |
| **What You Changed + Why** | Chose the snapshot-and-slice approach over having each agent return its own cost -- the `CostTracker` is shared across the whole batch, so slicing `calls[start:]` is the only way to attribute calls to ONE request without threading a per-request tracker through every agent signature. Tested the slice specifically against a **batch** run (all three requests), not just a single file: each result showed exactly its own 3 calls with distinct costs ($0.0164 / $0.0210 / $0.0263) rather than the cumulative 3/6/9 a naive global sum would have produced -- the isolation is the whole point of the requirement and the easy bug to miss. |

## Instance 9: Web UI -- FastAPI backend + React/GOV.UK frontend

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-25 |
| **Task** | Build a UI to visualise the pipeline: a FastAPI backend (`api/`) wrapping the existing agents, and a React + Vite + GOV.UK Design System frontend (`web/`) using TanStack Query, with a mock LLM so the demo needs no API key. |
| **What AI Generated** | `api/mock_client.py` (a duck-typed `MockChatClient.invoke()` returning request-aware JSON/letter content plus `usage_metadata`), `api/pipeline.py` (service layer reusing the real `triage/compliance/response` agents + RAG, holding in-memory state), and `api/main.py` (FastAPI routes + CORS + startup indexing). Frontend: typed `fetch` client, TanStack Query hooks (`useRequests`/`useProcess`/`useDecide`), a dashboard table, and a request-detail page rendering classification, compliance citations, draft letter, cost table, and an approve/reject/modify gate -- all using GOV.UK markup classes. |
| **What You Changed + Why** | Split the human-in-the-loop gate into two HTTP phases (`process` -> `awaiting_decision` -> `decide`) because the CLI gate blocks on `input()`, which can't work over a request/response API -- the browser holds the pause instead, and `decide` writes the same timestamped `decisions.log` so the audit trail is shared with the CLI. Wired the mock client through the **real** agents rather than faking responses at the API layer, so RAG retrieval, cost tracking, and fallbacks all still execute and the demo reflects true pipeline behaviour. Reused the cost snapshot pattern from Req 6 with a fresh per-request `CostTracker` (no batch sharing here, so no slice needed). On the frontend, fixed two real build failures found by actually running `npm run build`: `tsconfig.node.json` needed `composite: true` and emit enabled for project references, and the GOV.UK CSS 404'd on `/assets/fonts` until I copied the design-system assets into `public/` via a `postinstall` step. Verified the whole stack end-to-end through the Vite proxy (process -> draft -> decide, CSS + fonts 200) before calling it done -- noted the dev server fell back to port 5174 because 5173 was already taken. |
