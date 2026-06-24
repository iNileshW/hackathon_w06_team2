"""Agent functions for FOI request processing.

Each agent is a function that takes typed inputs and returns a dictionary.
The supervisor orchestrates the pipeline.
"""

import json

from indexer import search_policies
from cost_tracker import CostTracker
from langchain_anthropic import ChatAnthropic

MODEL_NAME = "claude-sonnet-4-5"


def _parse_json(content: str) -> dict:
    """Extract a JSON object from an LLM response, tolerating ```json fences."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return json.loads(text)


def triage_agent(request_text: str, client, cost_tracker: CostTracker) -> dict:
    """Classify an FOI request by topic and complexity.

    Args:
        request_text: The full text of the FOI request.
        client: A LangChain ChatAnthropic instance (or any chat model with a
            compatible .invoke() interface).
        cost_tracker: The shared CostTracker for logging API calls.

    Returns:
        A dictionary with keys:
        - "topic": str (e.g., "spending", "staffing", "procurement")
        - "complexity": str ("high", "medium", or "low")
        - "summary": str (one-sentence summary of what is being requested)

    TODO:
        1. Build a messages list (a system message with classification
           instructions, plus a user message containing request_text) and
           call client.invoke(messages).
        2. Parse response.content into the return format.
        3. Log the call with
           cost_tracker.log_call("triage", MODEL_NAME, response.usage_metadata).
        4. Handle errors: if the API call fails, return a fallback dict with
           topic="unknown", complexity="high", summary="Classification failed".
    """
    system = (
        "You are an FOI triage officer. Classify the request below.\n"
        "Respond with ONLY a JSON object, no prose, no markdown fences:\n"
        '{"topic": <one of: procurement, personal-data, financial, '
        'operational, policy, other>, '
        '"complexity": <one of: high, medium, low>, '
        '"summary": <one-sentence summary of what is requested>}'
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": request_text},
    ]
    try:
        response = client.invoke(messages)
        cost_tracker.log_call("triage", MODEL_NAME, response.usage_metadata)
        data = _parse_json(response.content)
        return {
            "topic": data.get("topic", "other"),
            "complexity": data.get("complexity", "high"),
            "summary": data.get("summary", ""),
        }
    except Exception as exc:
        print(f"  [triage] error, using fallback: {exc}")
        return {
            "topic": "unknown",
            "complexity": "high",
            "summary": "Classification failed",
        }


def compliance_agent(
    request_text: str,
    classification: dict,
    client,
    cost_tracker: CostTracker,
) -> dict:
    """Check the request against FOI policy using RAG retrieval.

    Args:
        request_text: The full text of the FOI request.
        classification: The output from triage_agent().
        client: A LangChain ChatAnthropic instance (or any chat model with a
            compatible .invoke() interface).
        cost_tracker: The shared CostTracker for logging API calls.

    Returns:
        A dictionary with keys:
        - "exemptions_found": list of str (exemption names/sections that may apply)
        - "reasoning": str (explanation of why each exemption applies or not)
        - "policy_sources": list of str (filenames of policy documents cited)
        - "recommendation": str ("release", "partial_release", or "withhold")

    TODO:
        1. Call search_policies(request_text) to retrieve relevant policy chunks.
        2. Build a prompt that includes the retrieved policy text as context,
           the request text, and the classification.
        3. Call client.invoke(messages) and parse response.content.
        4. Log the cost with response.usage_metadata.
        5. Handle errors with a fallback.
    """
    chunks = search_policies(request_text)
    sources = sorted({c["source"] for c in chunks})
    context = "\n\n".join(
        f"[{c['source']}]\n{c['text']}" for c in chunks
    ) or "(no policy excerpts retrieved)"

    system = (
        "You are an FOI compliance officer applying the Freedom of Information "
        "Act 2000. Using ONLY the policy excerpts provided, decide which "
        "exemptions may apply.\n"
        "Respond with ONLY a JSON object, no prose, no markdown fences:\n"
        '{"exemptions_found": [<section labels e.g. "s40", "s43">], '
        '"reasoning": <why each applies or not, citing the excerpts>, '
        '"recommendation": <one of: release, partial_release, withhold>}'
    )
    user = (
        f"REQUEST:\n{request_text}\n\n"
        f"CLASSIFICATION:\n{json.dumps(classification)}\n\n"
        f"POLICY EXCERPTS:\n{context}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        response = client.invoke(messages)
        cost_tracker.log_call("compliance", MODEL_NAME, response.usage_metadata)
        data = _parse_json(response.content)
        return {
            "exemptions_found": data.get("exemptions_found", []),
            "reasoning": data.get("reasoning", ""),
            "policy_sources": sources,
            "recommendation": data.get("recommendation", "withhold"),
        }
    except Exception as exc:
        print(f"  [compliance] error, using fallback: {exc}")
        return {
            "exemptions_found": [],
            "reasoning": "Compliance check failed",
            "policy_sources": sources,
            "recommendation": "withhold",
        }


def response_agent(
    request_text: str,
    classification: dict,
    compliance: dict,
    client,
    cost_tracker: CostTracker,
) -> dict:
    """Draft a response to the FOI request.

    Args:
        request_text: The full text of the FOI request.
        classification: The output from triage_agent().
        compliance: The output from compliance_agent().
        client: A LangChain ChatAnthropic instance (or any chat model with a
            compatible .invoke() interface).
        cost_tracker: The shared CostTracker for logging API calls.

    Returns:
        A dictionary with keys:
        - "draft_response": str (the full text of the draft response letter)
        - "evidence_summary": str (summary of classification and compliance findings
          for the human reviewer)

    TODO:
        1. Build a prompt that includes the request, classification, and
           compliance findings.
        2. Instruct the model to draft a formal FOI response letter.
        3. Log the cost with response.usage_metadata.
        4. Handle errors with a fallback.
    """
    system = (
        "You are an FOI response drafter. Write a formal, professional reply to "
        "the requester under the Freedom of Information Act 2000. Reflect the "
        "compliance recommendation: explain any exemptions applied and, where "
        "relevant, the public interest test. Output only the letter text."
    )
    user = (
        f"REQUEST:\n{request_text}\n\n"
        f"CLASSIFICATION:\n{json.dumps(classification)}\n\n"
        f"COMPLIANCE FINDINGS:\n{json.dumps(compliance)}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    evidence_summary = (
        f"Topic: {classification.get('topic')} "
        f"(complexity: {classification.get('complexity')}). "
        f"Exemptions: {compliance.get('exemptions_found')}. "
        f"Recommendation: {compliance.get('recommendation')}. "
        f"Policy sources: {compliance.get('policy_sources')}."
    )
    try:
        response = client.invoke(messages)
        cost_tracker.log_call("response", MODEL_NAME, response.usage_metadata)
        return {
            "draft_response": response.content,
            "evidence_summary": evidence_summary,
        }
    except Exception as exc:
        print(f"  [response] error, using fallback: {exc}")
        return {
            "draft_response": "[draft unavailable -- drafting failed]",
            "evidence_summary": evidence_summary,
        }


def human_checkpoint(draft: dict, request_file: str) -> dict:
    """Pause for human review and approval.

    Args:
        draft: The output from response_agent().
        request_file: The filename of the original request (for display).

    Returns:
        A dictionary with keys:
        - "decision": str ("approved", "rejected", or "modified")
        - "notes": str (operator's notes, empty string if none)

    TODO:
        1. Print the draft response and evidence summary to stdout.
        2. Prompt the operator: "Decision for {request_file} [approve/reject/modify]: "
        3. If "modify", prompt for notes.
        4. Return the decision dictionary.
    """
    print(f"\n--- Review for {request_file} ---")
    print("Draft response: [not implemented]")
    print("Evidence: [not implemented]")
    return {"decision": "approved", "notes": "Auto-approved (not implemented)"}


def supervisor(
    request_text: str,
    request_file: str,
    client,
    cost_tracker: CostTracker,
) -> dict:
    """Orchestrate the full processing pipeline for one FOI request.

    Args:
        request_text: The full text of the FOI request.
        request_file: The filename of the request (for logging and output).
        client: A LangChain ChatAnthropic instance (or any chat model with a
            compatible .invoke() interface).
        cost_tracker: The shared CostTracker for logging API calls.

    Returns:
        A dictionary containing all results from each pipeline stage,
        the human decision, and cost data for this request.

    TODO:
        1. Call triage_agent().
        2. Call compliance_agent() with the triage output.
        3. Call response_agent() with triage and compliance outputs.
        4. Call human_checkpoint().
        5. Assemble and return the full result dictionary.
        6. Wrap each step in try/except to handle failures gracefully.
    """
    try:
        classification = triage_agent(request_text, client, cost_tracker)
    except Exception as exc:
        print(f"  [supervisor] triage stage failed: {exc}")
        classification = {"topic": "unknown", "complexity": "high", "summary": "Classification failed"}

    try:
        compliance = compliance_agent(request_text, classification, client, cost_tracker)
    except Exception as exc:
        print(f"  [supervisor] compliance stage failed: {exc}")
        compliance = {"exemptions_found": [], "reasoning": "Compliance check failed", "policy_sources": [], "recommendation": "withhold"}

    try:
        draft = response_agent(request_text, classification, compliance, client, cost_tracker)
    except Exception as exc:
        print(f"  [supervisor] response stage failed: {exc}")
        draft = {"draft_response": "[draft unavailable]", "evidence_summary": "Drafting failed"}

    try:
        decision = human_checkpoint(draft, request_file)
    except Exception as exc:
        print(f"  [supervisor] checkpoint failed: {exc}")
        decision = {"decision": "rejected", "notes": f"Checkpoint error: {exc}"}

    return {
        "request_file": request_file,
        "classification": classification,
        "compliance": compliance,
        "draft_response": draft,
        "human_decision": decision,
    }
