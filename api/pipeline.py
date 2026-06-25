"""Service layer bridging the FastAPI routes and the existing agent pipeline.

Reuses the real triage/compliance/response agents (agents.py) and RAG indexer
(indexer.py), but swaps the interactive stdin approval gate for a two-phase
HTTP flow:

    process(id)  -> runs the three agents (mock LLM), produces a draft, parks
                    the request in "awaiting_decision"
    decide(id)   -> applies approve/reject/modify, appends a timestamped entry
                    to the shared decisions.log, finalises the request

State is held in-process (a dict) -- fine for a single-user demo.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Make the repo-root modules (agents, indexer, cost_tracker) importable
# regardless of where uvicorn is launched from.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents import (  # noqa: E402
    triage_agent,
    compliance_agent,
    response_agent,
    DECISION_LOG,
    MODEL_NAME,
)
from cost_tracker import CostTracker  # noqa: E402
from indexer import index_policies, search_policies  # noqa: E402

from .mock_client import MockChatClient  # noqa: E402

REQUESTS_DIR = ROOT / "documents" / "foi_requests"
POLICIES_DIR = ROOT / "documents" / "policies"
VALID_DECISIONS = {"approve", "reject", "modify"}

_client = MockChatClient()
_store: dict[str, dict] = {}


def ensure_index() -> int:
    """Index policies once if the vector store is empty, so RAG citations work."""
    if search_policies("freedom of information exemption"):
        return -1  # already populated
    return index_policies(str(POLICIES_DIR))


def _base_record(path: Path) -> dict:
    """A not-yet-processed request entry."""
    return {
        "id": path.stem,
        "filename": path.name,
        "request_text": path.read_text(),
        "status": "pending",
        "classification": None,
        "compliance": None,
        "draft_response": None,
        "evidence_summary": None,
        "cost_breakdown": None,
        "human_decision": None,
    }


def list_requests() -> list[dict]:
    """All sample requests, merged with any in-memory processing state."""
    out = []
    for path in sorted(REQUESTS_DIR.glob("*.txt")):
        out.append(_store.get(path.stem) or _base_record(path))
    return out


def get_request(request_id: str) -> dict | None:
    if request_id in _store:
        return _store[request_id]
    path = REQUESTS_DIR / f"{request_id}.txt"
    return _base_record(path) if path.exists() else None


def process(request_id: str) -> dict | None:
    """Run triage -> compliance -> response (mock LLM); park awaiting a decision."""
    record = get_request(request_id)
    if record is None:
        return None

    text = record["request_text"]
    tracker = CostTracker()

    classification = triage_agent(text, _client, tracker)
    compliance = compliance_agent(text, classification, _client, tracker)
    draft = response_agent(text, classification, compliance, _client, tracker)

    record.update(
        {
            "status": "awaiting_decision",
            "classification": classification,
            "compliance": compliance,
            "draft_response": draft["draft_response"],
            "evidence_summary": draft["evidence_summary"],
            "cost_breakdown": {
                "calls": tracker.calls,
                "total_tokens": sum(c["total_tokens"] for c in tracker.calls),
                "total_cost_usd": sum(c["estimated_cost_usd"] for c in tracker.calls),
                "model": MODEL_NAME,
            },
            "human_decision": None,
        }
    )
    _store[request_id] = record
    return record


def decide(request_id: str, decision: str, notes: str = "") -> dict | None:
    """Apply an approve/reject/modify decision and append it to the audit log.

    Returns None if the request is unknown; raises ValueError for an invalid
    decision or a request that has not been drafted yet.
    """
    record = _store.get(request_id)
    if record is None and (REQUESTS_DIR / f"{request_id}.txt").exists():
        raise ValueError("request has not been processed yet")
    if record is None:
        return None
    if record["status"] == "pending":
        raise ValueError("request has not been processed yet")
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of {sorted(VALID_DECISIONS)}")

    evidence_refs = (record.get("compliance") or {}).get("policy_sources", [])
    human_decision = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "decision": decision,
        "notes": notes or "",
        "evidence_refs": evidence_refs,
    }
    # Append to the same JSONL audit log the CLI uses.
    try:
        with open(DECISION_LOG, "a") as f:
            import json

            f.write(json.dumps(human_decision) + "\n")
    except Exception as exc:  # never let logging failure break the response
        print(f"[pipeline] decision log write failed: {exc}")

    record["status"] = {"approve": "approved", "reject": "rejected", "modify": "modified"}[decision]
    record["human_decision"] = human_decision
    _store[request_id] = record
    return record
