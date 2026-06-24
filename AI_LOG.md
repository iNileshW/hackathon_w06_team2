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

## Instance 3

| Field | Detail |
|-------|--------|
| **Date** | |
| **Task** | |
| **What AI Generated** | |
| **What You Changed + Why** | |
