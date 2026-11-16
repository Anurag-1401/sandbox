
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  ArrowLeft,
  ArrowDownToLine,
  Clock3,
  FileText,
  RefreshCw,
  UploadCloud
} from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { DocumentStatus } from "./DocumentStatus";

import {
  documentsApi,
  type DocumentItem,
  type DocumentVersion
} from "./documents-api";

import { getApiErrorMessage } from "../../lib/api";


export function DocumentDetailPage() {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadDocument = useCallback(async () => {
    if (!documentId) return;

    setLoading(true);
    setError(null);

    try {
      const [detail, versionResult] = await Promise.all([
        documentsApi.detail(documentId),
        documentsApi.versions(documentId)
      ]);

      setDocument(detail);
      setVersions(versionResult.items);
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    void loadDocument();
  }, [loadDocument]);

  async function uploadNewVersion(file: File) {
    if (!documentId) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setError("The selected file exceeds the 50 MB limit.");
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    setMessage(null);

    try {
      const result = await documentsApi.uploadVersion(
        documentId,
        file,
        setProgress
      );

      setMessage(
        `Version created successfully. ${result.chunks_indexed} chunks indexed.`
      );

      await loadDocument();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }

  async function downloadVersion(version: DocumentVersion) {
    if (!documentId) return;

    try {
      const blob = await documentsApi.download(
        documentId,
        version.id
      );

      const url = URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");

      anchor.href = url;
      anchor.download =
        `${document?.title || "document"}-v${version.version_number}.pdf`;

      window.document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      URL.revokeObjectURL(url);
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    }
  }

  if (loading) {
    return <div className="page-loading">Loading document details...</div>;
  }

  if (!document) {
    return (
      <div className="document-empty-state">
        <h3>Document unavailable</h3>
        <p>{error || "The requested document could not be found."}</p>
        <button
          className="secondary-button"
          onClick={() => navigate("/documents")}
        >
          <ArrowLeft size={15} />
          Back to library
        </button>
      </div>
    );
  }

  return (
    <div className="document-detail-page">
      <button
        className="back-link"
        type="button"
        onClick={() => navigate("/documents")}
      >
        <ArrowLeft size={15} />
        Back to document library
      </button>

      <PageHeader
        eyebrow="DOCUMENT INTELLIGENCE"
        title={document.title}
        description={document.source_filename}
        actions={
          <button
            className="secondary-button"
            type="button"
            onClick={() => void loadDocument()}
          >
            <RefreshCw size={15} />
            Refresh
          </button>
        }
      />

      {error && <div className="form-alert error">{error}</div>}
      {message && <div className="form-alert success">{message}</div>}

      <div className="document-overview-grid">
        <article className="document-overview-card">
          <span>Document status</span>
          <DocumentStatus status={document.status} />
        </article>

        <article className="document-overview-card">
          <span>Latest version</span>
          <strong>
            {document.latest_version_number
              ? `Version ${document.latest_version_number}`
              : "Not available"}
          </strong>
        </article>

        <article className="document-overview-card">
          <span>Total versions</span>
          <strong>{document.version_count}</strong>
        </article>

        <article className="document-overview-card">
          <span>Indexed chunks</span>
          <strong>{document.chunk_count.toLocaleString()}</strong>
        </article>
      </div>

      <section className="settings-card version-section">
        <div className="settings-card-heading">
          <div className="settings-card-icon">
            <Clock3 size={20} />
          </div>

          <div>
            <h2>Version history</h2>
            <p>
              Review indexed versions and download their original PDFs.
            </p>
          </div>

          <div className="version-section-action">
            <button
              className="primary-button"
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
            >
              <UploadCloud size={15} />
              Add version
            </button>

            <input
              ref={inputRef}
              hidden
              type="file"
              accept=".pdf,application/pdf"
              onChange={(event) => {
                const file = event.target.files?.[0];

                if (file) void uploadNewVersion(file);

                event.target.value = "";
              }}
            />
          </div>
        </div>

        {uploading && (
          <div className="version-upload-progress">
            <div className="version-upload-progress-copy">
              <span>Uploading and indexing new version...</span>
              <strong>{progress}%</strong>
            </div>
            <div className="upload-progress">
              <div style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}

        {versions.length === 0 ? (
          <div className="empty-state compact">
            <h3>No versions found</h3>
            <p>There are no versions available for this document.</p>
          </div>
        ) : (
          <div className="version-list">
            {versions.map((version) => (
              <article className="version-row" key={version.id}>
                <div className="version-file-icon">
                  <FileText size={19} />
                </div>

                <div className="version-main">
                  <strong>Version {version.version_number}</strong>
                  <span>
                    {new Date(version.created_at).toLocaleString()}
                  </span>
                  <code className="version-hash">
                    SHA-256: {version.content_hash}
                  </code>
                </div>

                <div className="version-metadata">
                  <DocumentStatus status={version.status} />
                  <span>{version.chunk_count} chunks</span>
                </div>

                <button
                  type="button"
                  className="secondary-button download-version"
                  onClick={() => void downloadVersion(version)}
                >
                  <ArrowDownToLine size={15} />
                  Download
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
