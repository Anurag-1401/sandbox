
import { api } from "../../lib/api";

export type InvestigationStatus =
  | "draft"
  | "queued"
  | "planning"
  | "researching"
  | "analyzing"
  | "comparing"
  | "verifying"
  | "review_required"
  | "approved"
  | "rejected"
  | "failed";

export type ReviewDecision =
  | "approve"
  | "reject"
  | "request_changes";

export interface InvestigationScope {
  jurisdiction?: string;
  industry?: string;
  effective_date?: string;
  regulatory_area?: string;
  additional_context?: string;
  document_ids?: string[];
}

export interface Investigation {
  id: string;
  title: string;
  question: string;
  scope: Record<string, unknown>;
  status: InvestigationStatus;
  created_at: string;
  updated_at: string;
}

export interface InvestigationCreateRequest {
  title: string;
  question: string;
  scope: InvestigationScope;
  document_ids: string[];
}

export interface InvestigationStartRequest {
  force_new_run: boolean;
}

export interface InvestigationRun {
  id: string;
  investigation_id: string;
  status: InvestigationStatus;
  state: Record<string, any>;
  result: Record<string, any>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface InvestigationEvent {
  id: string;
  event_type: string;
  description: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface InvestigationDetail {
  investigation: Investigation;
  latest_run: InvestigationRun | null;
  events: InvestigationEvent[];
}

export interface InvestigationReviewRequest {
  decision: ReviewDecision;
  comments: string;
}

export interface InvestigationReviewResponse {
  investigation_id: string;
  run_id: string;
  decision: ReviewDecision;
  status: InvestigationStatus;
}

export interface Finding {
  finding_id: string;
  category: string;
  statement: string;
  evidence_ids: string[];
  confidence_label: string;
  review_required: boolean;
}

export interface EvidenceRecord {
  evidence_id: string;
  chunk_id: string;
  document_id: string;
  version_id: string;
  document_title: string;
  version_number: number;
  page_start: number;
  page_end: number;
  content: string;
  retrieval_score: number | null;
  task_id: string;
}

export interface VerificationIssue {
  issue_type: string;
  description: string;
  finding_id: string | null;
  evidence_ids: string[];
}

export interface ClaimVerification {
  claim_id: string;
  verdict: "supported" | "contradicted" | "insufficient";
  rationale: string;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  limitations: string[];
}

export interface AtomicClaim {
  claim_id: string;
  text: string;
  claim_type: string;
  source_finding_ids: string[];
  evidence_ids: string[];
  entity: string | null;
  jurisdiction: string | null;
  temporal_scope: string | null;
}

export interface Contradiction {
  contradiction_id: string;
  claim_a_id: string;
  claim_b_id: string;
  description: string;
  severity: "high" | "medium" | "low";
  evidence_ids: string[];
  temporal_conflict: boolean;
  resolution_status: string;
}

export interface IntelligenceSummary {
  total_claims: number;
  supported_claims: number;
  contradicted_claims: number;
  insufficient_claims: number;
  contradictions_detected: number;
  applicable_claims: number;
  not_applicable_claims: number;
  uncertain_applicability: number;
  human_review_required: boolean;
}

export interface IntelligenceReport {
  schema_version: string;
  generated_at?: string;
  summary: IntelligenceSummary;
  claims: AtomicClaim[];
  verifications: ClaimVerification[];
  contradictions: Contradiction[];
  source_quality: Record<string, any>[];
  applicability: Record<string, any>[];
  confidence: Record<string, any>[];
  limitations: string[];
  human_review_required: boolean;
}

export interface InvestigationReport {
  title?: string;
  question?: string;
  summary?: string;
  findings?: Finding[];
  comparisons?: Record<string, any>[];
  evidence?: EvidenceRecord[];
  verification_issues?: VerificationIssue[];
  approved_finding_ids?: string[];
  limitations?: string[];
  human_review_required?: boolean;
  intelligence?: IntelligenceReport;
  model_intelligence?: Record<string, any>;
  generated_at?: string;
  [key: string]: any;
}

export async function listInvestigations(
  limit = 50,
  offset = 0
): Promise<Investigation[]> {
  const response = await api.get<Investigation[]>(
    "/investigations/",
    {
      params: { limit, offset }
    }
  );

  return response.data;
}

export async function createInvestigation(
  payload: InvestigationCreateRequest
): Promise<Investigation> {
  const response = await api.post<Investigation>(
    "/investigations/",
    payload
  );

  return response.data;
}

export async function getInvestigation(
  investigationId: string
): Promise<InvestigationDetail> {
  const response = await api.get<InvestigationDetail>(
    `/investigations/${investigationId}`
  );

  return response.data;
}

export async function executeInvestigation(
  investigationId: string,
  forceNewRun = false
): Promise<InvestigationRun> {
  const response = await api.post<InvestigationRun>(
    `/investigations/${investigationId}/execute`,
    {
      force_new_run: forceNewRun
    },
    {
      // The current backend runs the LangGraph workflow synchronously.
      // Do not impose the normal 60-second API-client timeout here.
      timeout: 0
    }
  );

  return response.data;
}

export async function getInvestigationRun(
  investigationId: string,
  runId: string
): Promise<InvestigationRun> {
  const response = await api.get<InvestigationRun>(
    `/investigations/${investigationId}/runs/${runId}`
  );

  return response.data;
}

export async function reviewInvestigation(
  investigationId: string,
  runId: string,
  payload: InvestigationReviewRequest
): Promise<InvestigationReviewResponse> {
  const response = await api.post<InvestigationReviewResponse>(
    `/investigations/${investigationId}/runs/${runId}/review`,
    payload
  );

  return response.data;
}
