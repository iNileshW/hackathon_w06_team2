# FOI Automation API

FastAPI backend that exposes the existing multi-agent FOI pipeline
(`agents.py`, `indexer.py`, `cost_tracker.py`) to the React UI in `../web`.

For the demo it runs the pipeline against a **mock LLM client**
(`mock_client.py`) — no Anthropic key and no spend — while still exercising
the real agents, RAG retrieval, cost tracking, and decision logging.

## Run

From the **repo root** (so `agents`/`indexer` import correctly):

```bash
pip install -r api/requirements.txt        # into the project .venv
uvicorn api.main:app --reload --port 8000
```

On startup the policy documents are indexed into ChromaDB once (so compliance
citations work).

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/api/health` | liveness |
| GET  | `/api/requests` | list all sample requests + processing state |
| GET  | `/api/requests/{id}` | one request |
| POST | `/api/requests/{id}/process` | run triage → compliance → response (mock), park awaiting decision |
| POST | `/api/requests/{id}/decision` | apply `approve`/`reject`/`modify`, append to `decisions.log` |

`decision` body: `{"decision": "approve" | "reject" | "modify", "notes": "..."}`

## Two-phase human-in-the-loop

The CLI gate blocks on `input()`. For the web UI it is split:

1. `process` produces the draft and sets status `awaiting_decision`.
2. `decide` records the operator's choice with a UTC timestamp and the policy
   citations as `evidence_refs`, appended to the same `decisions.log` the CLI uses.

State is held in-process (single-user demo).
