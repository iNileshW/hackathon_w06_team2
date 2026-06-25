"""Deterministic mock LLM client for the demo UI.

Implements the same duck-typed interface the real ChatAnthropic client exposes
to the agents (`.invoke(messages)` -> object with `.content` and
`.usage_metadata`), but returns canned, request-aware output instead of calling
the API. This lets the web UI exercise the full triage -> compliance -> response
pipeline (and the cost tracker) with no API key and no spend.

The agent is identified from its system prompt; the response is shaped to match
what each agent's parser expects (JSON for triage/compliance, letter text for
response).
"""

import json
from dataclasses import dataclass


@dataclass
class MockResponse:
    """Mimics a LangChain AIMessage: carries content and token usage."""

    content: str
    usage_metadata: dict


def _classify(request_text: str) -> dict:
    """Keyword-rule triage so each sample request gets a distinct, plausible label."""
    t = request_text.lower()
    if any(k in t for k in ("disciplinary", "staff member", "anonymised", "personal")):
        topic, complexity = "personal-data", "medium"
        summary = "Request for aggregated staff disciplinary data and anonymised outcomes."
    elif any(k in t for k in ("tender", "evaluation", "scoring", "correspondence")):
        topic, complexity = "procurement", "high"
        summary = "Request for internal correspondence and tender evaluation records for a contract award."
    elif any(k in t for k in ("consultancy", "contract", "supplier", "procurement")):
        topic, complexity = "procurement", "medium"
        summary = "Request for spend and contract details on external consultancy engagements."
    elif any(k in t for k in ("budget", "spend", "financial", "expenditure")):
        topic, complexity = "financial", "medium"
        summary = "Request for departmental financial expenditure figures."
    else:
        topic, complexity = "other", "low"
        summary = "General information request."
    return {"topic": topic, "complexity": complexity, "summary": summary}


def _comply(user_text: str) -> dict:
    """Canned exemption analysis keyed off the classification embedded in the prompt."""
    t = user_text.lower()
    if "personal-data" in t:
        return {
            "exemptions_found": ["s40"],
            "reasoning": (
                "Section 40 (personal information) is engaged because the request touches "
                "staff records. Aggregated and anonymised figures can be released, but any "
                "field allowing an individual to be identified must be withheld."
            ),
            "recommendation": "partial_release",
        }
    if "procurement" in t or "financial" in t:
        return {
            "exemptions_found": ["s43"],
            "reasoning": (
                "Section 43 (commercial interests) may apply to supplier pricing and tender "
                "scoring data, where disclosure would prejudice commercial interests. The "
                "public interest in procurement transparency is weighed against that prejudice; "
                "contract values and supplier names are generally releasable."
            ),
            "recommendation": "partial_release",
        }
    return {
        "exemptions_found": [],
        "reasoning": "No exemptions identified against the retrieved policy excerpts; the information is releasable.",
        "recommendation": "release",
    }


def _draft(user_text: str) -> str:
    """A formal FOI reply letter; reflects the recommendation present in the prompt."""
    t = user_text.lower()
    if "withhold" in t:
        stance = (
            "After review under the Freedom of Information Act 2000, the requested information "
            "is exempt from disclosure and is being withheld."
        )
    elif "partial_release" in t:
        stance = (
            "Following review under the Freedom of Information Act 2000, we are able to disclose "
            "the majority of the information requested. Certain elements are exempt and have been "
            "redacted; the relevant exemptions and the public interest test are explained below."
        )
    else:
        stance = (
            "I can confirm that the department holds the information you have requested, and it is "
            "released to you in full. No exemptions under the Freedom of Information Act 2000 apply."
        )
    return (
        "Dear Requester,\n\n"
        "Freedom of Information Act 2000 - Response to your request\n\n"
        "Thank you for your request. " + stance + "\n\n"
        "If you are dissatisfied with the handling of your request you may ask for an internal "
        "review, and you may subsequently complain to the Information Commissioner's Office.\n\n"
        "Yours sincerely,\n"
        "Freedom of Information Team"
    )


class MockChatClient:
    """Drop-in stand-in for ChatAnthropic used by the agents during the demo."""

    def invoke(self, messages):
        system = ""
        user = ""
        for m in messages:
            role = m.get("role")
            if role == "system":
                system = m.get("content", "")
            elif role == "user":
                user = m.get("content", "")

        if "triage officer" in system:
            content = json.dumps(_classify(user))
        elif "compliance officer" in system:
            content = json.dumps(_comply(user))
        else:  # response drafter
            content = _draft(user)

        # Plausible token usage so the cost tracker reports realistic numbers.
        input_tokens = max(1, (len(system) + len(user)) // 4)
        output_tokens = max(1, len(content) // 4)
        return MockResponse(
            content=content,
            usage_metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
        )
