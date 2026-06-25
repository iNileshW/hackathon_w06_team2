export type Status =
  | "pending"
  | "awaiting_decision"
  | "approved"
  | "rejected"
  | "modified";

export interface Classification {
  topic: string;
  complexity: string;
  summary: string;
}

export interface Compliance {
  exemptions_found: string[];
  reasoning: string;
  policy_sources: string[];
  recommendation: string;
}

export interface CostCall {
  agent: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface CostBreakdown {
  calls: CostCall[];
  total_tokens: number;
  total_cost_usd: number;
  model: string;
}

export interface HumanDecision {
  timestamp: string;
  request_id: string;
  decision: string;
  notes: string;
  evidence_refs: string[];
}

export interface FoiRequest {
  id: string;
  filename: string;
  request_text: string;
  status: Status;
  classification: Classification | null;
  compliance: Compliance | null;
  draft_response: string | null;
  evidence_summary: string | null;
  cost_breakdown: CostBreakdown | null;
  human_decision: HumanDecision | null;
}

export type Decision = "approve" | "reject" | "modify";
