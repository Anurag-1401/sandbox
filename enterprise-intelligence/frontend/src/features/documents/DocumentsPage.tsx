
import {
  useCallback,
  useEffect,
  useRef,
  useState
} from "react";
import type { ChangeEvent, DragEvent } from "react";

import {
  ChevronLeft,
  ChevronRight,
  FileText,
  FolderOpen,
  RefreshCw,
  Search,
  UploadCloud,
  X
} from "lucide-react";

import { Link } from "react-router-dom";

import { PageHeader } from "../../components/ui/PageHeader";
import { DocumentStatus } from "./DocumentStatus";

import {
  documentsApi,
  type DocumentItem,
  type DocumentUploadResponse
} from "./documents-api";

import { getApiErrorMessage } from "../../lib/api";


const PAGE_SIZE = 20;
const MAX_FILE_SIZE_MB = 50;


interface UploadEntry {
  id: string;
  file: File;
  progress: number;
  status: "queued" | "uploading" | "complete" | "failed";
  message?: string;
}


export function DocumentsPage() {
  const inputRef = useRef<HTMLInputElement>(null);

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [uploads, setUploads] = useState<UploadEntry[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const [uploadResults, setUploadResults] = useState<
    DocumentUploadResponse[]
  >([]);

  const loadDocuments = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true);
    else setLoading(true);

    setError(null);

    try {
      const result = await documentsApi.list({
        q: search.trim() || undefined,
        status: statusFilter || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE
      });

      setDocuments(result.items);
      setTotal(result.total);
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [search, statusFilter, page]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  function updateUpload(
    id: string,
    changes: Partial<UploadEntry>
  ) {
    setUploads((current) =>
      current.map((item) =>
        item.id === id ? { ...item, ...changes } : item
      )
    );
  }

  async function processFiles(fileList: FileList | File[]) {
    const files = Array.from(fileList);

    if (files.length === 0) return;

    const queued: UploadEntry[] = [];

    for (const file of files) {
      const id = crypto.randomUUID();

      if (file.type !== "application/pdf" &&
          !file.name.toLowerCase().endsWith(".pdf")) {
        queued.push({
          id,
          file,
          progress: 0,
          status: "failed",
          message: "Only PDF files are supported."
        });

        continue;
      }

      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        queued.push({
          id,
          file,
          progress: 0,
          status: "failed",
          message: `File exceeds ${MAX_FILE_SIZE_MB} MB.`
        });

        continue;
      }

      queued.push({
        id,
        file,
        progress: 0,
        status: "queued"
      });
    }

    setUploads((current) => [...queued, ...current]);
    setUploadResults([]);

    for (const entry of queued) {
      if (entry.status === "failed") continue;

      updateUpload(entry.id, {
        status: "uploading",
        progress: 0
      });

      try {
        const result = await documentsApi.upload(
          entry.file,
          (percentage) => {
            updateUpload(entry.id, { progress: percentage });
          }
        );

        setUploadResults((current) => [result, ...current]);

        updateUpload(entry.id, {
          status: "complete",
          progress: 100,
          message: result.message
        });
      } catch (cause) {
        updateUpload(entry.id, {
          status: "failed",
          message: getApiErrorMessage(cause)
        });
      }
    }

    await loadDocuments(true);
  }

  function onInputChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    if (event.target.files) {
      void processFiles(event.target.files);
      event.target.value = "";
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);

    if (event.dataTransfer.files) {
      void processFiles(event.dataTransfer.files);
    }
  }

  function clearUploads() {
    setUploads([]);
    setUploadResults([]);
  }

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="documents-page">
      <PageHeader
        eyebrow="DOCUMENT INTELLIGENCE"
        title="Document library"
        description="Upload, organize and inspect documents indexed in your organization workspace."
        actions={
          <button
            type="button"
            className="primary-button"
            onClick={() => inputRef.current?.click()}
          >
            <UploadCloud size={16} />
            Upload PDF
          </button>
        }
      />

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        multiple
        hidden
        onChange={onInputChange}
      />

      <div
        className={`document-dropzone ${isDragging ? "dragging" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
      >
        <div className="dropzone-icon">
          <UploadCloud size={23} />
        </div>

        <div className="dropzone-copy">
          <strong>Drag and drop PDF files here</strong>
          <span>
            or{" "}
            <button
              type="button"
              className="inline-link"
              onClick={() => inputRef.current?.click()}
            >
              browse files
            </button>
          </span>
          <small>
            PDF only · Maximum {MAX_FILE_SIZE_MB} MB per file
          </small>
        </div>
      </div>

      {uploads.length > 0 && (
        <section className="upload-queue-card">
          <div className="upload-queue-heading">
            <div>
              <h2>Upload queue</h2>
              <p>
                {uploads.filter((item) => item.status === "complete").length}
                {" "}completed ·{" "}
                {uploads.filter((item) => item.status === "failed").length}
                {" "}failed
              </p>
            </div>

            <button
              className="icon-button light"
              type="button"
              aria-label="Clear upload queue"
              onClick={clearUploads}
            >
              <X size={17} />
            </button>
          </div>

          <div className="upload-queue-list">
            {uploads.map((item) => (
              <div className="upload-item" key={item.id}>
                <div className="upload-file-icon">
                  <FileText size={18} />
                </div>

                <div className="upload-file-copy">
                  <strong>{item.file.name}</strong>
                  <span>
                    {(item.file.size / (1024 * 1024)).toFixed(2)} MB
                    {" · "}
                    {item.status}
                  </span>

                  {item.status === "uploading" && (
                    <div className="upload-progress">
                      <div
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  )}

                  {item.message && (
                    <small className={
                      item.status === "failed"
                        ? "upload-error"
                        : "upload-success"
                    }>
                      {item.message}
                    </small>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {uploadResults.length > 0 && (
        <div className="form-alert success">
          {uploadResults.length} document(s) successfully processed and indexed.
        </div>
      )}

      <div className="document-library-heading">
        <div>
          <h2>All documents</h2>
          <p>{total.toLocaleString()} documents in this workspace</p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={() => void loadDocuments(true)}
          disabled={refreshing}
        >
          <RefreshCw size={14} />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="document-toolbar">
        <div className="document-search">
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(0);
            }}
            placeholder="Search by title or filename..."
          />
        </div>

        <select
          value={statusFilter}
          onChange={(event) => {
            setStatusFilter(event.target.value);
            setPage(0);
          }}
          aria-label="Filter by processing status"
        >
          <option value="">All statuses</option>
          <option value="indexed">Indexed</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {error && <div className="form-alert error">{error}</div>}

      <div className="document-table-card">
        {loading ? (
          <div className="page-loading">Loading document library...</div>
        ) : documents.length === 0 ? (
          <div className="document-empty-state">
            <div className="empty-state-icon">
              <FolderOpen size={24} />
            </div>
            <h3>No documents found</h3>
            <p>
              Upload a PDF to begin extracting, chunking and indexing
              document content.
            </p>
            <button
              className="primary-button"
              type="button"
              onClick={() => inputRef.current?.click()}
            >
              <UploadCloud size={15} />
              Upload first document
            </button>
          </div>
        ) : (
          <>
            <div className="table-scroll">
              <table className="data-table document-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Status</th>
                    <th>Latest version</th>
                    <th>Chunks</th>
                    <th>Visibility</th>
                    <th>Last updated</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {documents.map((document) => (
                    <tr key={document.id}>
                      <td>
                        <div className="document-name-cell">
                          <div className="document-row-icon">
                            <FileText size={17} />
                          </div>

                          <div>
                            <Link
                              className="document-title-link"
                              to={`/documents/${document.id}`}
                            >
                              {document.title}
                            </Link>
                            <span className="table-subtext">
                              {document.source_filename}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <DocumentStatus status={document.status} />
                      </td>

                      <td>
                        {document.latest_version_number
                          ? `v${document.latest_version_number}`
                          : "—"}
                      </td>

                      <td>
                        {document.chunk_count.toLocaleString()}
                      </td>

                      <td className="capitalize">
                        {document.visibility}
                      </td>

                      <td>
                        {new Date(
                          document.updated_at
                        ).toLocaleDateString()}
                      </td>

                      <td>
                        <Link
                          className="table-open-link"
                          to={`/documents/${document.id}`}
                        >
                          Open
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="document-pagination">
              <span>
                Showing {page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, total)} of {total}
              </span>

              <div>
                <button
                  type="button"
                  className="pagination-button"
                  disabled={page <= 0}
                  onClick={() => setPage((value) => value - 1)}
                  aria-label="Previous page"
                >
                  <ChevronLeft size={16} />
                </button>

                <span>{page + 1} / {pageCount}</span>

                <button
                  type="button"
                  className="pagination-button"
                  disabled={page + 1 >= pageCount}
                  onClick={() => setPage((value) => value + 1)}
                  aria-label="Next page"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
