
import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  AlertCircle,
  ChevronRight,
  ClipboardList,
  FileSearch,
  LoaderCircle,
  Plus,
  RefreshCw,
  Search,
  X
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { getApiErrorMessage } from "../../lib/api";

import {
  createInvestigation,
  listInvestigations,
  type Investigation,
  type InvestigationCreateRequest,
  type InvestigationScope
} from "./investigations-api";

const initialForm = {
  title: "",
  question: "",
  jurisdiction: "",
  industry: "",
  regulatoryArea: "",
  effectiveDate: "",
  additionalContext: "",
  documentIds: ""
};

function statusAppearance(status: string) {
  if (["approved"].includes(status)) return "success" as const;
  if (["review_required", "verifying"].includes(status)) {
    return "warning" as const;
  }
  if (["failed", "rejected"].includes(status)) {
    return "danger" as const;
  }
  if (["queued", "planning", "researching", "analyzing", "comparing"].includes(status)) {
    return "info" as const;
  }
  return "neutral" as const;
}

function readableStatus(status: string) {
  return status.replaceAll("_", " ");
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString();
}

export function InvestigationsPage() {
  const navigate = useNavigate();

  const [items, setItems] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState(initialForm);

  const loadInvestigations = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    setError("");

    try {
      const data = await listInvestigations(100, 0);
      setItems(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadInvestigations();
  }, [loadInvestigations]);

  const filteredItems = items.filter((item) => {
    const term = search.trim().toLowerCase();

    const matchesSearch =
      !term ||
      item.title.toLowerCase().includes(term) ||
      item.question.toLowerCase().includes(term);

    const matchesStatus =
      statusFilter === "all" || item.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  function updateField(
    field: keyof typeof initialForm,
    value: string
  ) {
    setForm((current) => ({
      ...current,
      [field]: value
    }));
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");

    const title = form.title.trim();
    const question = form.question.trim();

    if (title.length < 3) {
      setFormError("The investigation title must contain at least 3 characters.");
      return;
    }

    if (question.length < 10) {
      setFormError("The investigation question must contain at least 10 characters.");
      return;
    }

    const documentIds = form.documentIds
      .split(/[\n,;]+/)
      .map((value) => value.trim())
      .filter(Boolean);

    const uuidPattern =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    const invalidId = documentIds.find((id) => !uuidPattern.test(id));

    if (invalidId) {
      setFormError(`Invalid document UUID: ${invalidId}`);
      return;
    }

    if (documentIds.length > 100) {
      setFormError("A maximum of 100 document IDs can be selected.");
      return;
    }

    const scope: InvestigationScope = {};

    if (form.jurisdiction.trim()) {
      scope.jurisdiction = form.jurisdiction.trim();
    }

    if (form.industry.trim()) {
      scope.industry = form.industry.trim();
    }

    if (form.regulatoryArea.trim()) {
      scope.regulatory_area = form.regulatoryArea.trim();
    }

    if (form.effectiveDate) {
      scope.effective_date = form.effectiveDate;
    }

    if (form.additionalContext.trim()) {
      scope.additional_context = form.additionalContext.trim();
    }

    const payload: InvestigationCreateRequest = {
      title,
      question,
      scope,
      document_ids: documentIds
    };

    setSaving(true);

    try {
      const created = await createInvestigation(payload);

      setModalOpen(false);
      setForm(initialForm);

      navigate(`/investigations/${created.id}`);
    } catch (err) {
      setFormError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="f5-page">
      <PageHeader
        eyebrow="INVESTIGATION OPERATIONS"
        title="Investigation Center"
        description="Create, execute and monitor evidence-based investigations across your accessible document collection."
        actions={
          <button
            type="button"
            className="f5-primary-button"
            onClick={() => {
              setFormError("");
              setModalOpen(true);
            }}
          >
            <Plus size={16} />
            New investigation
          </button>
        }
      />

      <div className="f5-metric-row">
        <article className="f5-stat-card">
          <span>Total investigations</span>
          <strong>{items.length}</strong>
          <small>Visible in this organization</small>
        </article>

        <article className="f5-stat-card">
          <span>Awaiting review</span>
          <strong>
            {items.filter((item) => item.status === "review_required").length}
          </strong>
          <small>Require human decision</small>
        </article>

        <article className="f5-stat-card">
          <span>Approved</span>
          <strong>
            {items.filter((item) => item.status === "approved").length}
          </strong>
          <small>Reviewed investigations</small>
        </article>

        <article className="f5-stat-card">
          <span>Failed</span>
          <strong>
            {items.filter((item) => item.status === "failed").length}
          </strong>
          <small>Execution failures</small>
        </article>
      </div>

      <section className="f5-panel">
        <div className="f5-toolbar">
          <div>
            <h2>Investigation records</h2>
            <p>Open an investigation to inspect its run, evidence and review status.</p>
          </div>

          <button
            type="button"
            className="f5-icon-button"
            onClick={() => void loadInvestigations(true)}
            disabled={refreshing}
            aria-label="Refresh investigations"
            title="Refresh"
          >
            {refreshing ? (
              <LoaderCircle size={17} className="f5-spin" />
            ) : (
              <RefreshCw size={17} />
            )}
          </button>
        </div>

        <div className="f5-filters">
          <label className="f5-search-box">
            <Search size={16} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search title or investigation question..."
            />
          </label>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter by status"
          >
            <option value="all">All statuses</option>
            <option value="draft">Draft</option>
            <option value="queued">Queued</option>
            <option value="planning">Planning</option>
            <option value="researching">Researching</option>
            <option value="analyzing">Analyzing</option>
            <option value="comparing">Comparing</option>
            <option value="verifying">Verifying</option>
            <option value="review_required">Review required</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {error && (
          <div className="f5-alert f5-alert-error" role="alert">
            <AlertCircle size={17} />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="f5-loading">
            <LoaderCircle className="f5-spin" size={25} />
            <span>Loading investigations...</span>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="f5-empty">
            <div className="f5-empty-icon">
              <ClipboardList size={24} />
            </div>
            <h3>
              {items.length === 0
                ? "No investigations created"
                : "No matching investigations"}
            </h3>
            <p>
              {items.length === 0
                ? "Create an investigation to begin a structured research and verification workflow."
                : "Try changing the search phrase or status filter."}
            </p>
            {items.length === 0 && (
              <button
                type="button"
                className="f5-primary-button"
                onClick={() => setModalOpen(true)}
              >
                <Plus size={15} />
                Create investigation
              </button>
            )}
          </div>
        ) : (
          <div className="f5-table-wrap">
            <table className="f5-table">
              <thead>
                <tr>
                  <th>Investigation</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Last updated</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredItems.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => navigate(`/investigations/${item.id}`)}
                    className="f5-clickable-row"
                  >
                    <td>
                      <div className="f5-record-title">
                        <span className="f5-record-icon">
                          <FileSearch size={17} />
                        </span>
                        <span>
                          <strong>{item.title}</strong>
                          <small>{item.question}</small>
                        </span>
                      </div>
                    </td>

                    <td>
                      <StatusBadge status={statusAppearance(item.status)}>
                        {readableStatus(item.status)}
                      </StatusBadge>
                    </td>

                    <td>{formatDate(item.created_at)}</td>
                    <td>{formatDate(item.updated_at)}</td>

                    <td>
                      <ChevronRight size={17} className="f5-row-chevron" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {modalOpen && (
        <div
          className="f5-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !saving) {
              setModalOpen(false);
            }
          }}
        >
          <section
            className="f5-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="f5-create-title"
          >
            <div className="f5-modal-header">
              <div>
                <span className="f5-eyebrow">NEW WORKFLOW</span>
                <h2 id="f5-create-title">Create investigation</h2>
                <p>Define the research question and investigation scope.</p>
              </div>

              <button
                type="button"
                className="f5-icon-button"
                onClick={() => setModalOpen(false)}
                disabled={saving}
                aria-label="Close dialog"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="f5-form">
              <label className="f5-field">
                <span>Investigation title *</span>
                <input
                  value={form.title}
                  onChange={(event) => updateField("title", event.target.value)}
                  placeholder="e.g. Data retention compliance review"
                  minLength={3}
                  maxLength={300}
                  required
                />
              </label>

              <label className="f5-field">
                <span>Research question *</span>
                <textarea
                  value={form.question}
                  onChange={(event) => updateField("question", event.target.value)}
                  placeholder="What do you need to investigate, compare or verify?"
                  minLength={10}
                  maxLength={4000}
                  rows={4}
                  required
                />
              </label>

              <div className="f5-form-grid">
                <label className="f5-field">
                  <span>Jurisdiction</span>
                  <input
                    value={form.jurisdiction}
                    onChange={(event) =>
                      updateField("jurisdiction", event.target.value)
                    }
                    placeholder="e.g. India"
                  />
                </label>

                <label className="f5-field">
                  <span>Industry</span>
                  <input
                    value={form.industry}
                    onChange={(event) =>
                      updateField("industry", event.target.value)
                    }
                    placeholder="e.g. Financial services"
                  />
                </label>

                <label className="f5-field">
                  <span>Regulatory area</span>
                  <input
                    value={form.regulatoryArea}
                    onChange={(event) =>
                      updateField("regulatoryArea", event.target.value)
                    }
                    placeholder="e.g. Data protection"
                  />
                </label>

                <label className="f5-field">
                  <span>Effective date</span>
                  <input
                    type="date"
                    value={form.effectiveDate}
                    onChange={(event) =>
                      updateField("effectiveDate", event.target.value)
                    }
                  />
                </label>
              </div>

              <label className="f5-field">
                <span>Additional context</span>
                <textarea
                  value={form.additionalContext}
                  onChange={(event) =>
                    updateField("additionalContext", event.target.value)
                  }
                  placeholder="Optional background or constraints..."
                  rows={3}
                />
              </label>

              <label className="f5-field">
                <span>Document IDs (optional)</span>
                <textarea
                  value={form.documentIds}
                  onChange={(event) =>
                    updateField("documentIds", event.target.value)
                  }
                  placeholder="Paste document UUIDs separated by commas or new lines"
                  rows={3}
                />
                <small>
                  Only documents accessible to your organization can be used.
                  Leave empty to search the accessible document collection.
                </small>
              </label>

              {formError && (
                <div className="f5-alert f5-alert-error" role="alert">
                  <AlertCircle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="f5-modal-actions">
                <button
                  type="button"
                  className="f5-secondary-button"
                  onClick={() => setModalOpen(false)}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="f5-primary-button"
                  disabled={saving}
                >
                  {saving ? (
                    <LoaderCircle size={16} className="f5-spin" />
                  ) : (
                    <Plus size={16} />
                  )}
                  Create investigation
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
