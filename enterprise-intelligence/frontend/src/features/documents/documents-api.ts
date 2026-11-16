
import { api } from "../../lib/api";

export type DocumentStatus =
  | "uploaded"
  | "processing"
  | "indexed"
  | "failed";

export interface DocumentItem {
  id: string;
  title: string;
  source_filename: string;
  status: DocumentStatus | string;
  visibility: string;
  created_at: string;
  updated_at: string;
  latest_version_number: number | null;
  latest_version_status: string | null;
  version_count: number;
  chunk_count: number;
}

export interface DocumentListResponse {
  items: DocumentItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_number: number;
  content_hash: string;
  status: string;
  created_at: string;
  chunk_count: number;
}

export interface DocumentVersionListResponse {
  items: DocumentVersion[];
  total: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  version_id: string;
  title: string;
  filename: string;
  sha256: string;
  pages_extracted: number;
  chunks_indexed: number;
  embedding_dimension: number;
  status: string;
  message: string;
}

export interface DocumentProcessingSummary {
  total_documents: number;
  indexed_documents: number;
  processing_documents: number;
  failed_documents: number;
  total_versions: number;
  total_chunks: number;
}

export const documentsApi = {
  async list(params?: {
    q?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<DocumentListResponse> {
    const response = await api.get<DocumentListResponse>(
      "/documents",
      { params }
    );

    return response.data;
  },

  async summary(): Promise<DocumentProcessingSummary> {
    const response = await api.get<DocumentProcessingSummary>(
      "/documents/summary"
    );

    return response.data;
  },

  async detail(documentId: string): Promise<DocumentItem> {
    const response = await api.get<DocumentItem>(
      `/documents/${documentId}`
    );

    return response.data;
  },

  async versions(
    documentId: string
  ): Promise<DocumentVersionListResponse> {
    const response = await api.get<DocumentVersionListResponse>(
      `/documents/${documentId}/versions`
    );

    return response.data;
  },

  async upload(
    file: File,
    onProgress?: (percentage: number) => void
  ): Promise<DocumentUploadResponse> {
    const form = new FormData();
    form.append("file", file);

    const response = await api.post<DocumentUploadResponse>(
      "/documents/upload",
      form,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        },
        onUploadProgress(event) {
          if (!event.total) return;

          const percentage = Math.round(
            (event.loaded / event.total) * 100
          );

          onProgress?.(percentage);
        }
      }
    );

    return response.data;
  },

  async uploadVersion(
    documentId: string,
    file: File,
    onProgress?: (percentage: number) => void
  ): Promise<DocumentUploadResponse> {
    const form = new FormData();
    form.append("file", file);

    const response = await api.post<DocumentUploadResponse>(
      `/documents/${documentId}/versions`,
      form,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        },
        onUploadProgress(event) {
          if (!event.total) return;

          onProgress?.(
            Math.round((event.loaded / event.total) * 100)
          );
        }
      }
    );

    return response.data;
  },

  async download(
    documentId: string,
    versionId: string
  ): Promise<Blob> {
    const response = await api.get(
      `/documents/${documentId}/versions/${versionId}/download`,
      {
        responseType: "blob"
      }
    );

    return response.data as Blob;
  }
};
