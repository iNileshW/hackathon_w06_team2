Project Brief
Your department receives dozens of Freedom of Information (FOI) requests each month. Each
request follows a defined workflow: log the request, classify it by topic and complexity, check
whether any exemptions apply under the Freedom of Information Act 2000, draft a response, and
obtain senior approval before release. Today this process is manual, handled by a small team who
spend most of their time on repetitive classification and exemption-checking steps.
You will build a multi-agent system that automates the repeatable parts of this workflow. A triage
agent classifies incoming requests. A compliance agent checks requests against policy documents
using RAG. A response drafting agent composes a reply based on the triage and compliance
findings. A supervisor orchestrates the pipeline and enforces human-in-the-loop checkpoints at
critical decision points – no response leaves the system without human approval.
The system runs as a CLI application. It processes a folder of FOI request files, produces a
structured output for each request, and logs cost and decision data throughout

Requirements
1. At least two collaborating agents with distinct roles (e.g., triage, compliance, response drafting)
orchestrated by a supervisor
2. RAG integration: a compliance agent retrieves relevant excerpts from policy documents stored
in ChromaDB before making exemption recommendations
3. Human-in-the-loop: the system implements an approval gate using the approve/reject/modify
pattern from the w05 pre-read; the gate pauses execution, displays evidence, accepts the
operator’s decision, and writes a timestamped decision log entry
4. Error handling: if an agent fails (API error, unparseable response, empty result), the system logs
the error and continues with a fallback rather than crashing
5. Cost tracking: every LLM call logs the model used, prompt tokens, completion tokens, and
estimated cost; a summary prints at the end of each run
6. Structured output: each processed request produces a JSON result with fields for
classification, exemption findings, draft response, human decision, and cost breakdown
7. An AI_LOG.md file documenting three or more instances of AI-assisted development. Use the
seeded template at labs/hackathon/starter/AI_LOG.md; complete four fields for each instance:
Date, Task, What AI Generated, What You Changed + Why


Minimum Viable Submission
The MVS defines the floor for a complete demonstrable system. A team that ships these four
items with a clear demo has met the bar.
1. Triage agent classifies one FOI request with minimal structured output – one field per pipeline
stage (e.g., {"topic": "personal-data"} from triage, {"exemption": "s40"} from compliance). Rich
multi-field JSON is a stretch goal, not a floor requirement.
2. Compliance agent retrieves at least one policy chunk from ChromaDB and cites it in the
exemption analysis.
3. HITL approval gate pauses execution, displays the evidence to the operator, and accepts an
approve/reject/modify decision before the pipeline continues.
4. Cost summary prints at end-of-run showing model name and token breakdown per call.
Anything beyond these four items moves a submission from “met the bar” toward Excellent on
the rubric. Teams should reach MVS by the Day 1 checkpoint and use Day 2 to deepen coverage,
add error handling, and polish the demo.


For each of the tasks or each of the to-do, I want you to implement them based on the requirements. After each implementation, provide a summary of what was changed and explain to me in simple terms what was changed and why you went that route. Feel free to check previous implementations and the code to see if you can take a few things from there to update it or change anything.