
import { api } from "../../lib/api";
import type {
  GraphNode,
  NodeType,
  RelationType
} from "../knowledge-graph/knowledge-graph-api";

export type InvestigationStatus =
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type FindingType =
  | "obligation_impact"
  | "product_impact"
  | "organization_impact"
  | "evidence_gap"
  | "contradiction"
  | "related_entity";

export type FindingStatus =
  | "open"
  | "under_review"
  | "confirmed"
  | "dismissed";

export type FindingPriority =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational";

export type ReviewDecision =
  | "applicable"
  | "not_applicable"
  | "uncertain"
  | "insufficient_evidence";

export interface Investigation {
  id: string;
  title: string;
  description: string | null;
  status: InvestigationStatus;
  root_node_ids: string[];
  depth: number;
  summary: string | null;
  result_metadata: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface InvestigationFinding {
  id: string;
  run_id: string;
  node_id: string | null;
  finding_type: FindingType;
  priority: FindingPriority;
  priority_score: number;
  confidence: number | null;
  title: string;
  summary: string;
  status: FindingStatus;
  path_node_ids: string[];
  path_edge_ids: string[];
  evidence_ids: string[];
  details: Record<string, unknown>;
  review_decision: ReviewDecision | null;
  review_notes: string | null;
  created_at: string;
}

export interface InvestigationDetail {
  investigation: Investigation;
  findings: InvestigationFinding[];
}

export interface InvestigationCreateRequest {
  title: string;
  description?: string | null;
  root_node_ids: string[];
  depth: number;
  include_unverified: boolean;
  relationship_types: RelationType[];
  node_types: NodeType[];
  include_evidence: boolean;
}

export interface FindingReviewRequest {
  status: "under_review" | "confirmed" | "dismissed";
  review_decision?: ReviewDecision | null;
  review_notes?: string | null;
}

export const impactApi = {
  async listInvestigations(params?: {
    limit?: number;
    offset?: number;
  }): Promise<Investigation[]> {
    const response = await api.get<Investigation[]>(
      "/graph-investigations",
      { params }
    );
    return response.data;
  },

  async getInvestigation(id: string): Promise<InvestigationDetail> {
    const response = await api.get<InvestigationDetail>(
      `/graph-investigations/${id}`
    );
    return response.data;
  },

  async createInvestigation(
    payload: InvestigationCreateRequest
  ): Promise<InvestigationDetail> {
    const response = await api.post<InvestigationDetail>(
      "/graph-investigations",
      payload
    );
    return response.data;
  },

  async reviewFinding(
    findingId: string,
    payload: FindingReviewRequest
  ): Promise<InvestigationFinding> {
    const response = await api.patch<InvestigationFinding>(
      `/graph-investigations/findings/${findingId}`,
      payload
    );
    return response.data;
  },

  async searchNodes(params?: {
    q?: string;
    node_type?: NodeType | "";
    limit?: number;
    offset?: number;
  }): Promise<{ items: GraphNode[]; total: number }> {
    const response = await api.get<{ items: GraphNode[]; total: number }>(
      "/knowledge-graph/nodes",
      { params }
    );
    return response.data;
  }
};

export const FINDING_TYPE_LABELS: Record<FindingType, string> = {
  obligation_impact: "Obligation impact",
  product_impact: "Product impact",
  organization_impact: "Organization impact",
  evidence_gap: "Evidence gap",
  contradiction: "Contradiction",
  related_entity: "Related entity"
};

export const REVIEW_DECISION_LABELS: Record<ReviewDecision, string> = {
  applicable: "Applicable",
  not_applicable: "Not applicable",
  uncertain: "Uncertain",
  insufficient_evidence: "Insufficient evidence"
};
