
import { api } from "../../lib/api";

export const NODE_TYPES = [
  "regulation",
  "clause",
  "amendment",
  "obligation",
  "standard",
  "product",
  "organization",
  "authority",
  "concept"
] as const;

export const RELATION_TYPES = [
  "contains",
  "amends",
  "supersedes",
  "repeals",
  "requires",
  "applies_to",
  "references",
  "defines",
  "issued_by",
  "governs",
  "implements",
  "conflicts_with",
  "related_to",
  "derived_from"
] as const;

export type NodeType = typeof NODE_TYPES[number];
export type RelationType = typeof RELATION_TYPES[number];
export type VerificationStatus =
  | "unverified"
  | "reviewed"
  | "verified"
  | "rejected";

export interface GraphNode {
  id: string;
  organization_id: string;
  node_type: NodeType;
  name: string;
  canonical_key: string;
  external_identifier: string | null;
  description: string | null;
  jurisdiction: string | null;
  aliases: string[];
  properties: Record<string, unknown>;
  verification_status: VerificationStatus;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface GraphEdge {
  id: string;
  organization_id: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: RelationType;
  description: string | null;
  properties: Record<string, unknown>;
  verification_status: VerificationStatus;
  confidence: number | null;
  created_at: string;
}

export interface GraphEvidence {
  id: string;
  organization_id: string;
  node_id: string | null;
  edge_id: string | null;
  document_id: string;
  version_id: string;
  chunk_id: string | null;
  page_number: number | null;
  quote: string;
  evidence_role: "supports" | "contradicts" | "contextualizes";
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface GraphSearchResponse {
  items: GraphNode[];
  total: number;
}

export interface GraphNeighborhood {
  root: GraphNode;
  nodes: GraphNode[];
  edges: GraphEdge[];
  depth: number;
}

export interface NodeCreateRequest {
  node_type: NodeType;
  name: string;
  canonical_key?: string | null;
  external_identifier?: string | null;
  description?: string | null;
  jurisdiction?: string | null;
  aliases: string[];
  properties: Record<string, unknown>;
  confidence?: number | null;
}

export interface EdgeCreateRequest {
  source_node_id: string;
  target_node_id: string;
  relation_type: RelationType;
  description?: string | null;
  properties: Record<string, unknown>;
  confidence?: number | null;
}

export interface EvidenceCreateRequest {
  node_id?: string | null;
  edge_id?: string | null;
  document_id: string;
  version_id: string;
  chunk_id?: string | null;
  page_number?: number | null;
  quote: string;
  evidence_role: "supports" | "contradicts" | "contextualizes";
  metadata_json: Record<string, unknown>;
}

export const knowledgeGraphApi = {
  async searchNodes(params: {
    q?: string;
    node_type?: NodeType | "";
    limit?: number;
    offset?: number;
  }): Promise<GraphSearchResponse> {
    const response = await api.get<GraphSearchResponse>(
      "/knowledge-graph/nodes",
      { params }
    );
    return response.data;
  },

  async getNode(id: string): Promise<GraphNode> {
    const response = await api.get<GraphNode>(
      `/knowledge-graph/nodes/${id}`
    );
    return response.data;
  },

  async getNeighborhood(
    id: string,
    depth: number,
    includeUnverified: boolean
  ): Promise<GraphNeighborhood> {
    const response = await api.get<GraphNeighborhood>(
      `/knowledge-graph/nodes/${id}/neighborhood`,
      {
        params: {
          depth,
          include_unverified: includeUnverified
        }
      }
    );
    return response.data;
  },

  async createNode(payload: NodeCreateRequest): Promise<GraphNode> {
    const response = await api.post<GraphNode>(
      "/knowledge-graph/nodes",
      payload
    );
    return response.data;
  },

  async createEdge(payload: EdgeCreateRequest): Promise<GraphEdge> {
    const response = await api.post<GraphEdge>(
      "/knowledge-graph/edges",
      payload
    );
    return response.data;
  },

  async getNodeEvidence(id: string): Promise<GraphEvidence[]> {
    const response = await api.get<GraphEvidence[]>(
      `/knowledge-graph/nodes/${id}/evidence`
    );
    return response.data;
  },

  async addEvidence(
    payload: EvidenceCreateRequest
  ): Promise<GraphEvidence> {
    const response = await api.post<GraphEvidence>(
      "/knowledge-graph/evidence",
      payload
    );
    return response.data;
  },

  async verifyNode(
    id: string,
    status: VerificationStatus
  ): Promise<GraphNode> {
    const response = await api.patch<GraphNode>(
      `/knowledge-graph/nodes/${id}/verification`,
      { status }
    );
    return response.data;
  },

  async verifyEdge(
    id: string,
    status: VerificationStatus
  ): Promise<GraphEdge> {
    const response = await api.patch<GraphEdge>(
      `/knowledge-graph/edges/${id}/verification`,
      { status }
    );
    return response.data;
  }
};
