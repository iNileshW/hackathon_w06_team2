# AI Assistance Log

Record every instance where you use AI to generate, refactor, or debug code. Four fields per entry: what you asked for, what the AI produced, what you changed, and why you changed it.

## Instance 1: Triage agent classification prompt

| Field | Detail |
|-------|--------|
| **Date** | YYYY-MM-DD |
| **Task** | Scaffolded the triage agent's classification prompt for FOI request categorisation |
| **What AI Generated** | System prompt with 5 topic categories (personal-data, environmental, financial, operational, policy). Classification output as free-text paragraph. Did not include complexity rating. Used ambiguous phrasing ("try to classify") rather than a structured output format. |
| **What You Changed + Why** | Changed output format from free-text to JSON (`{"topic": "...", "complexity": "high|medium|low"}`) -- structured output is required by the supervisor for downstream routing. Added complexity field (high/medium/low) -- compliance agent needs this to decide retrieval depth. Changed "try to classify" to "classify the following request" -- hedging language produces unreliable output. Added a fallback category ("other") -- requests that do not fit the five categories should not crash the pipeline. |

## Instance 2

| Field | Detail |
|-------|--------|
| **Date** | |
| **Task** | |
| **What AI Generated** | |
| **What You Changed + Why** | |

## Instance 3

| Field | Detail |
|-------|--------|
| **Date** | |
| **Task** | |
| **What AI Generated** | |
| **What You Changed + Why** | |
