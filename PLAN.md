# FOI Automation — Build Plan

Maps each project requirement to concrete work in the existing scaffold. Scaffold runs out of the box with placeholder output; every item below replaces a stub or adds new code.

## Scaffold map

| File | Holds | Stub status |
|------|-------|-------------|
| `main.py` | CLI entry (`index`, `process`), file loop, output writing | Done — wires everything |
| `agents.py` | `triage_agent`, `compliance_agent`, `response_agent`, `human_checkpoint`, `supervisor` | All stubbed |
| `indexer.py` | `chunk_text` (done), `index_policies`, `search_policies` | RAG stubbed |
| `cost_tracker.py` | `CostTracker.log_call`, `summary`, `print_summary` | Cost calc stubbed |
| `AI_LOG.md` | AI-assist log, instance 1 seeded | 2 instances empty |
| `documents/policies/` | 2 policy docs (exemptions guide, data handling) | Source data |
| `documents/foi_requests/` | 3 sample requests | Test input |
| `examples/checkpoint-reference.txt` | Target output shape | Reference |

Build order: **indexer → cost_tracker → agents (triage → compliance → response → checkpoint → supervisor) → AI_LOG**. RAG and cost must work before agents can use them.

---

## Req 1 — Multi-agent + supervisor

Three role agents orchestrated by supervisor. Scaffold already has the function signatures and wiring.

**Files:** `agents.py`

**Plan**
- `triage_agent`: LLM classify → `{topic, complexity, summary}`. System prompt with fixed topic set (procurement, personal-data, financial, operational, policy, other) + complexity high/medium/low. Force JSON output (`response_format={"type":"json_object"}`).
- `compliance_agent`: consumes triage output, runs RAG (Req 2), returns `{exemptions_found, reasoning, policy_sources, recommendation}`.
- `response_agent`: consumes triage + compliance, drafts letter → `{draft_response, evidence_summary}`.
- `supervisor`: call triage → compliance → response → checkpoint in order, wrap **each** in try/except (Req 4), assemble final dict.

**Done when:** one request flows through all three agents and supervisor returns a populated dict.

---

## Req 2 — RAG over ChromaDB (compliance)

Compliance agent retrieves policy excerpts before recommending exemptions.

**Files:** `indexer.py`, `agents.py` (compliance), `main.py index` (already calls `index_policies`)

**Plan**
- `index_policies`: delete existing collection (try/except), create `foi_policies` collection, loop `*.txt` in policies dir, `chunk_text` each (already implemented, 400/80), `collection.add` with ids `f"{filename}-{i}"` and metadata `{"file": filename, "chunk_index": i}`. Return total chunks.
- `search_policies`: get collection (try/except → `[]`), `query(query_texts=[query], n_results=3)`, return `[{"text", "source"}]`.
- compliance agent: call `search_policies(request_text)`, inject retrieved text into prompt as context, **cite source filenames** in `policy_sources`.
- Embeddings: default chroma (sentence-transformers); if HF blocked set `EMBEDDING_PROVIDER=openai` per README.

**Done when:** `python main.py index` reports >0 chunks AND compliance output cites ≥1 policy source. (MVS floor: retrieve ≥1 chunk, cite it.)

---

## Req 3 — Human-in-the-loop approval gate

approve/reject/modify gate that pauses, shows evidence, logs timestamped decision.

**Files:** `agents.py` (`human_checkpoint`), new `decisions.log` (or JSONL)

**Plan**
- Print draft response + `evidence_summary` (classification + compliance + policy citations).
- Prompt: `Decision for {request_file} [approve/reject/modify]:`.
- `modify` → prompt for `notes`; reject → optional reason.
- Build decision dict: `{decision, notes, timestamp (UTC ISO8601), request_id, evidence_refs}`.
- **Append** timestamped entry to a decision log file (open `"a"`).
- No response leaves without passing this gate — supervisor must not skip it.

**Done when:** run pauses for input, accepts all three decisions, writes a dated log line per request. See `examples/checkpoint-reference.txt` for target shape.

---

## Req 4 — Error handling + fallback

Agent failure (API error, unparseable response, empty result) logs and continues, no crash.

**Files:** `agents.py` (all agents + supervisor)

**Plan**
- Each agent: try/except around LLM call. On failure log error, return documented fallback:
  - triage → `{topic:"unknown", complexity:"high", summary:"Classification failed"}`
  - compliance → `{exemptions_found:[], reasoning:"Compliance check failed", policy_sources:[], recommendation:"withhold"}` (fail safe = withhold)
  - response → `{draft_response:"[draft unavailable]", evidence_summary:"Drafting failed"}`
- Guard JSON parse: `try json.loads` → fallback on `JSONDecodeError`.
- Treat empty/None content as failure.
- Supervisor try/except per stage so one bad request doesn't kill the batch loop in `main.py`.

**Done when:** force an error (bad key / malformed text) → run completes, logs error, emits fallback JSON.

---

## Req 5 — Cost tracking

Every LLM call logs model + prompt/completion tokens + estimated cost. Summary at end.

**Files:** `cost_tracker.py`, every agent (call `log_call`)

**Plan**
- `log_call`: finish cost calc — lookup model in `MODEL_COSTS`, default `0.0` rates if absent, `cost = prompt/1000*p_rate + completion/1000*c_rate`. (summary/print already done.)
- Each agent after its LLM call: `cost_tracker.log_call(agent_name, model, response.usage)`.
- `main.py` already calls `tracker.print_summary()` at end.

**Done when:** summary prints per-agent model, token breakdown, total cost. (MVS floor: model name + token breakdown per call.)

---

## Req 6 — Structured JSON output

Each request → JSON with classification, exemption findings, draft, human decision, cost breakdown.

**Files:** `agents.py` (supervisor return), `main.py` (already writes `output/{stem}-result.json`)

**Plan**
- Supervisor return dict must include: `request_file`, `classification`, `compliance`, `draft_response`, `human_decision`, **`cost_breakdown`** (per-request slice of tracker — add this; scaffold dict currently omits it).
- For per-request cost, snapshot `len(tracker.calls)` before processing and slice after, or have supervisor sum its own calls.

**Done when:** `output/request-00X-result.json` has all six field groups. (MVS floor: one field per stage; rich multi-field = stretch.)

---

## Req 7 — AI_LOG.md

≥3 documented AI-assist instances, 4 fields each (Date, Task, What AI Generated, What You Changed + Why).

**Files:** `AI_LOG.md` (instance 1 seeded, 2 & 3 empty)

**Plan**
- Fill instances 2 & 3 with real work from this build (e.g. RAG indexing, cost calc, error fallbacks).
- Each: real date, specific task, what AI produced, what you changed **and why** (the "why" is graded).
- Add more than 3 to push toward Excellent.

**Done when:** ≥3 complete instances, all 4 fields populated, why is specific not generic.

---

## MVS checkpoint (Day 1 floor)

Ship these four first, then deepen:
1. Triage classifies 1 request, minimal structured output (Req 1, partial).
2. Compliance retrieves ≥1 chunk + cites it (Req 2).
3. HITL gate pauses, shows evidence, takes approve/reject/modify (Req 3).
4. Cost summary prints model + tokens per call (Req 5).

Day 2: error handling (Req 4), rich JSON (Req 6), AI_LOG (Req 7), demo polish.

## Verify

```bash
python main.py index                              # >0 chunks
python main.py process documents/foi_requests/    # full pipeline, prompts, cost summary
cat output/request-001-result.json                # all 6 field groups
```
