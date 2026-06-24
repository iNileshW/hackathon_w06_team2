"""Agent functions for FOI request processing.

Each agent is a function that takes typed inputs and returns a dictionary.
The supervisor orchestrates the pipeline.
"""

from indexer import search_policies
from cost_tracker import CostTracker


def triage_agent(request_text: str, client, cost_tracker: CostTracker) -> dict:
    """Classify an FOI request by topic and complexity.

    Args:
        request_text: The full text of the FOI request.
        client: An OpenAI client instance.
        cost_tracker: The shared CostTracker for logging API calls.

    Returns:
        A dictionary with keys:
        - "topic": str (e.g., "spending", "staffing", "procurement")
        - "complexity": str ("high", "medium", or "low")
        - "summary": str (one-sentence summary of what is being requested)

    TODO:
        1. Call client.chat.completions.create() with a system prompt that
           instructs the model to classify the request.
        2. Parse the response into the return format.
        3. Log the call with cost_tracker.log_call("triage", model, response.usage).
        4. Handle errors: if the API call fails, return a fallback dict with
           topic="unknown", complexity="high", summary="Classification failed".
    """
    return {
        "topic": "unknown",
        "complexity": "medium",
        "summary": "Not implemented -- replace this stub.",
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
        client: An OpenAI client instance.
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
        3. Call the LLM and parse the response.
        4. Log the cost.
        5. Handle errors with a fallback.
    """
    return {
        "exemptions_found": [],
        "reasoning": "Not implemented -- replace this stub.",
        "policy_sources": [],
        "recommendation": "release",
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
        client: An OpenAI client instance.
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
        3. Log the cost.
        4. Handle errors with a fallback.
    """
    return {
        "draft_response": "Not implemented -- replace this stub.",
        "evidence_summary": "Not implemented.",
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
        client: An OpenAI client instance.
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
    classification = triage_agent(request_text, client, cost_tracker)
    compliance = compliance_agent(request_text, classification, client, cost_tracker)
    draft = response_agent(request_text, classification, compliance, client, cost_tracker)
    decision = human_checkpoint(draft, request_file)

    return {
        "request_file": request_file,
        "classification": classification,
        "compliance": compliance,
        "draft_response": draft,
        "human_decision": decision,
    }
