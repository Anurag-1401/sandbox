
import { api } from "./api";

export interface SearchRequest {
  query: string;
  top_k?: number;
  candidate_limit?: number;
  document_id?: string;
  version_id?: string;
  use_reranker?: boolean;
  match_mode?: "exact_phrase" | "hybrid";
}

export interface SearchEvidence {
  chunk_id: string;
  document_id: string;
  version_id: string;
  document_title: string;
  version_number: number;
  chunk_index: number;
  content: string;
  page_start: number;
  page_end: number;
  semantic_rank: number | null;
  keyword_rank: number | null;
  rrf_score: number;
  rerank_score: number | null;
  rerank_position: number | null;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  reranking_enabled: boolean;
  results: SearchEvidence[];
}

export interface RAGRequest {
  question: string;
  top_k?: number;
  candidate_limit?: number;
  document_id?: string;
  version_id?: string;
  use_reranker?: boolean;
}

export interface RAGFinding {
  text: string;
  evidence_ids: string[];
}

export interface RAGCitation {
  evidence_id: string;
  chunk_id: string;
  document_id: string;
  version_id: string;
  document_title: string;
  version_number: number;
  page_start: number;
  page_end: number;
  quoted_text: string;
}

export interface RAGResponse {
  question: string;
  answer: string;
  findings: RAGFinding[];
  citations: RAGCitation[];
  limitations: string[];
  insufficient_evidence: boolean;
  retrieval_count: number;
  model: string;
}

export async function searchDocuments(
  payload: SearchRequest
): Promise<SearchResponse> {
  const response = await api.post<SearchResponse>(
    "/search/",
    {
      query: payload.query,
      top_k: payload.top_k ?? 10,
      candidate_limit: payload.candidate_limit ?? 40,
      document_id: payload.document_id || undefined,
      version_id: payload.version_id || undefined,
      use_reranker: payload.use_reranker ?? true,
      match_mode: payload.match_mode ?? "exact_phrase"
    }
  );

  return response.data;
}

export async function askResearchAssistant(
  payload: RAGRequest
): Promise<RAGResponse> {
  const response = await api.post<RAGResponse>(
    "/rag/answer",
    {
      question: payload.question,
      top_k: payload.top_k ?? 8,
      candidate_limit: payload.candidate_limit ?? 40,
      document_id: payload.document_id || undefined,
      version_id: payload.version_id || undefined,
      use_reranker: payload.use_reranker ?? true,
    }
  );

  return response.data;
}
