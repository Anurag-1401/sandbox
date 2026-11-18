
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent
} from "react";
import {
  Activity,
  AlertCircle,
  ArrowDownToLine,
  Check,
  ChevronRight,
  CircleAlert,
  ClipboardList,
  FileSearch,
  Filter,
  LoaderCircle,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  X
} from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { getApiErrorMessage } from "../../lib/api";
import {
  impactApi,
  FINDING_TYPE_LABELS,
  REVIEW_DECISION_LABELS,
  type FindingPriority,
  type FindingStatus,
  type FindingType,
  type Investigation,
  type InvestigationDetail,
  type InvestigationFinding,
  type ReviewDecision
} from "./impact-api";

import type {
  GraphNode,
  NodeType,
  RelationType
} from "../knowledge-graph/knowledge-graph-api";

const NODE_TYPES: NodeType[] = [
  "regulation",
  "clause",
  "amendment",
  "obligation",
  "standard",
  "product",
  "organization",
  "authority",
  "concept"
];

const RELATION_TYPES: RelationType[] = [
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
];

const NODE_LABELS: Record<NodeType, string> = {
  regulation: "Regulation",
  clause: "Clause",
  amendment: "Amendment",
  obligation: "Obligation",
  standard: "Standard",
  product: "Product",
  organization: "Organization",
  authority: "Authority",
  concept: "Concept"
};

const RELATION_LABELS: Record<RelationType, string> = {
  contains: "Contains",
  amends: "Amends",
  supersedes: "Supersedes",
  repeals: "Repeals",
  requires: "Requires",
  applies_to: "Applies to",
  references: "References",
  defines: "Defines",
  issued_by: "Issued by",
  governs: "Governs",
  implements: "Implements",
  conflicts_with: "Conflicts with",
  related_to: "Related to",
  derived_from: "Derived from"
};

const PRIORITY_ORDER: FindingPriority[] = [
  "critical",
  "high",
  "medium",
  "low",
  "informational"
];

const FINDING_TYPES = Object.keys(
  FINDING_TYPE_LABELS
) as FindingType[];

function dateLabel(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString();
}

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) =>
    letter.toUpperCase()
  );
}

function PriorityBadge({ priority }: { priority: FindingPriority }) {
  return (
    <span className={`ia-priority ${priority}`}>
      <span />
      {titleCase(priority)}
    </span>
  );
}

function RunStatus({ status }: { status: Investigation["status"] }) {
  return (
    <span className={`ia-run-status ${status}`}>
      {titleCase(status)}
    </span>
  );
}

function FindingStatusBadge({ status }: { status: FindingStatus }) {
  return (
    <span className={`ia-finding-status ${status}`}>
      {titleCase(status)}
    </span>
  );
}

function CreateInvestigationPanel({
  onClose,
  onCreated
}: {
  onClose: () => void;
  onCreated: (detail: InvestigationDetail) => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [search, setSearch] = useState("");
  const [nodeResults, setNodeResults] = useState<GraphNode[]>([]);
  const [selectedRoots, setSelectedRoots] = useState<GraphNode[]>([]);
  const [depth, setDepth] = useState(2);
  const [includeUnverified, setIncludeUnverified] = useState(false);
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<NodeType[]>([]);
  const [selectedRelations, setSelectedRelations] = useState<RelationType[]>([]);
  const [loadingNodes, setLoadingNodes] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const searchNodes = useCallback(async () => {
    setLoadingNodes(true);
    setError("");

    try {
      const response = await impactApi.searchNodes({
        q: search.trim() || undefined,
        limit: 50,
        offset: 0
      });
      setNodeResults(response.items);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingNodes(false);
    }
  }, [search]);

  useEffect(() => {
    void searchNodes();
  }, [searchNodes]);

  function toggleRoot(node: GraphNode) {
    setSelectedRoots((current) => {
      if (current.some((item) => item.id === node.id)) {
        return current.filter((item) => item.id !== node.id);
      }

      if (current.length >= 10) {
        setError("You can select a maximum of 10 starting entities.");
        return current;
      }

      setError("");
      return [...current, node];
    });
  }

  function toggleNodeType(type: NodeType) {
    setSelectedNodeTypes((current) =>
      current.includes(type)
        ? current.filter((item) => item !== type)
        : [...current, type]
    );
  }

  function toggleRelation(type: RelationType) {
    setSelectedRelations((current) =>
      current.includes(type)
        ? current.filter((item) => item !== type)
        : [...current, type]
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (selectedRoots.length === 0) {
      setError("Select at least one starting entity.");
      return;
    }

    setCreating(true);

    try {
      const detail = await impactApi.createInvestigation({
        title: title.trim(),
        description: description.trim() || null,
        root_node_ids: selectedRoots.map((node) => node.id),
        depth,
        include_unverified: includeUnverified,
        include_evidence: includeEvidence,
        node_types: selectedNodeTypes,
        relationship_types: selectedRelations
      });

      onCreated(detail);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="ia-modal-backdrop" onMouseDown={onClose}>
      <section
        className="ia-modal ia-create-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ia-create-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="ia-modal-header">
          <div>
            <span className="ia-eyebrow">IMPACT ANALYSIS</span>
            <h2 id="ia-create-title">New investigation</h2>
            <p>Define the starting entities and graph traversal scope.</p>
          </div>
          <button className="ia-icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form className="ia-form" onSubmit={submit}>
          <label>
            Investigation title *
            <input
              required
              minLength={3}
              maxLength={500}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Product regulatory impact assessment"
            />
          </label>

          <label>
            Description
            <textarea
              rows={2}
              maxLength={10000}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Describe the objective and scope..."
            />
          </label>

          <div className="ia-field-heading">
            <div>
              <strong>Starting entities *</strong>
              <span>Select one to ten entities from the knowledge graph.</span>
            </div>
            <span className="ia-count">{selectedRoots.length}/10</span>
          </div>

          <div className="ia-root-search">
            <Search size={16} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search graph entities..."
            />
            <button
              type="button"
              onClick={() => void searchNodes()}
              aria-label="Search entities"
            >
              <RefreshCw size={15} />
            </button>
          </div>

          {selectedRoots.length > 0 && (
            <div className="ia-selected-roots">
              {selectedRoots.map((node) => (
                <span key={node.id}>
                  {node.name}
                  <button
                    type="button"
                    onClick={() => toggleRoot(node)}
                    aria-label={`Remove ${node.name}`}
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="ia-root-results">
            {loadingNodes ? (
              <div className="ia-empty-small">
                <LoaderCircle className="ia-spin" size={18} />
                Searching entities...
              </div>
            ) : nodeResults.length === 0 ? (
              <div className="ia-empty-small">No matching entities.</div>
            ) : (
              nodeResults.map((node) => {
                const selected = selectedRoots.some(
                  (item) => item.id === node.id
                );

                return (
                  <button
                    type="button"
                    key={node.id}
                    className={`ia-root-option ${selected ? "selected" : ""}`}
                    onClick={() => toggleRoot(node)}
                  >
                    <span className="ia-root-check">
                      {selected && <Check size={13} />}
                    </span>
                    <span className="ia-root-copy">
                      <strong>{node.name}</strong>
                      <small>
                        {NODE_LABELS[node.node_type]} · {titleCase(node.verification_status)}
                      </small>
                    </span>
                    <ChevronRight size={14} />
                  </button>
                );
              })
            )}
          </div>

          <div className="ia-form-grid">
            <label>
              Traversal depth
              <select
                value={depth}
                onChange={(event) => setDepth(Number(event.target.value))}
              >
                <option value={1}>1 level</option>
                <option value={2}>2 levels</option>
                <option value={3}>3 levels</option>
              </select>
            </label>
            <div className="ia-option-stack">
              <label className="ia-checkbox">
                <input
                  type="checkbox"
                  checked={includeUnverified}
                  onChange={(event) => setIncludeUnverified(event.target.checked)}
                />
                Include unverified graph records
              </label>
              <label className="ia-checkbox">
                <input
                  type="checkbox"
                  checked={includeEvidence}
                  onChange={(event) => setIncludeEvidence(event.target.checked)}
                />
                Include linked evidence
              </label>
            </div>
          </div>

          <details className="ia-filter-details">
            <summary><Filter size={14} /> Advanced graph filters</summary>

            <div className="ia-filter-group">
              <strong>Node types</strong>
              <div className="ia-checkbox-grid">
                {NODE_TYPES.map((type) => (
                  <label className="ia-checkbox" key={type}>
                    <input
                      type="checkbox"
                      checked={selectedNodeTypes.includes(type)}
                      onChange={() => toggleNodeType(type)}
                    />
                    {NODE_LABELS[type]}
                  </label>
                ))}
              </div>
              <small>Leave all unchecked to include every node type.</small>
            </div>

            <div className="ia-filter-group">
              <strong>Relationship types</strong>
              <div className="ia-checkbox-grid">
                {RELATION_TYPES.map((type) => (
                  <label className="ia-checkbox" key={type}>
                    <input
                      type="checkbox"
                      checked={selectedRelations.includes(type)}
                      onChange={() => toggleRelation(type)}
                    />
                    {RELATION_LABELS[type]}
                  </label>
                ))}
              </div>
              <small>Leave all unchecked to include every relationship type.</small>
            </div>
          </details>

          {error && <div className="ia-error"><AlertCircle size={15} />{error}</div>}

          <div className="ia-modal-actions">
            <button type="button" className="ia-button secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="ia-button primary" disabled={creating}>
              {creating
                ? <LoaderCircle className="ia-spin" size={16} />
                : <Activity size={16} />}
              Run impact analysis
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function FindingReviewPanel({
  finding,
  onClose,
  onSaved
}: {
  finding: InvestigationFinding;
  onClose: () => void;
  onSaved: (updated: InvestigationFinding) => void;
}) {
  const [status, setStatus] = useState<
    "under_review" | "confirmed" | "dismissed"
  >(
    finding.status === "open" ? "under_review" : finding.status
  );
  const [decision, setDecision] = useState<ReviewDecision | "">(
    finding.review_decision ?? ""
  );
  const [notes, setNotes] = useState(finding.review_notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (status === "confirmed" && !decision) {
      setError("A review decision is required to confirm a finding.");
      return;
    }

    setSaving(true);

    try {
      const updated = await impactApi.reviewFinding(finding.id, {
        status,
        review_decision: decision || null,
        review_notes: notes.trim() || null
      });

      onSaved(updated);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="ia-modal-backdrop" onMouseDown={onClose}>
      <section
        className="ia-modal ia-review-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ia-review-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="ia-modal-header">
          <div>
            <span className="ia-eyebrow">HUMAN REVIEW</span>
            <h2 id="ia-review-title">Review finding</h2>
            <p>{finding.title}</p>
          </div>
          <button className="ia-icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="ia-review-context">
          <PriorityBadge priority={finding.priority} />
          <span>Priority score: {Number(finding.priority_score).toFixed(2)}/100</span>
        </div>

        <form className="ia-form" onSubmit={submit}>
          <label>
            Review status *
            <select
              value={status}
              onChange={(event) =>
                setStatus(event.target.value as typeof status)
              }
            >
              <option value="under_review">Under review</option>
              <option value="confirmed">Confirmed</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </label>

          <label>
            Applicability / review decision
            <select
              value={decision}
              onChange={(event) =>
                setDecision(event.target.value as ReviewDecision | "")
              }
            >
              <option value="">Select decision</option>
              {(Object.keys(REVIEW_DECISION_LABELS) as ReviewDecision[]).map(
                (item) => (
                  <option key={item} value={item}>
                    {REVIEW_DECISION_LABELS[item]}
                  </option>
                )
              )}
            </select>
          </label>

          <label>
            Review notes
            <textarea
              rows={4}
              maxLength={10000}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Record the rationale, evidence considered, and remaining questions..."
            />
          </label>

          {status === "confirmed" && (
            <div className="ia-notice">
              A decision is required when confirming a finding. Confirmation records
              a human review outcome; it does not independently establish legal compliance.
            </div>
          )}

          {error && <div className="ia-error"><AlertCircle size={15} />{error}</div>}

          <div className="ia-modal-actions">
            <button type="button" className="ia-button secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="ia-button primary" disabled={saving}>
              {saving
                ? <LoaderCircle className="ia-spin" size={16} />
                : <ShieldCheck size={16} />}
              Save review
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function exportFindings(detail: InvestigationDetail) {
  const columns = [
    "finding_id",
    "finding_type",
    "title",
    "priority",
    "priority_score",
    "confidence",
    "status",
    "review_decision",
    "summary",
    "node_id",
    "evidence_ids"
  ];

  const escapeCsv = (value: unknown) => {
    const text = Array.isArray(value)
      ? value.join("; ")
      : String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  };

  const rows = detail.findings.map((finding) => [
    finding.id,
    finding.finding_type,
    finding.title,
    finding.priority,
    finding.priority_score,
    finding.confidence,
    finding.status,
    finding.review_decision,
    finding.summary,
    finding.node_id,
    finding.evidence_ids
  ]);

  const csv = [
    columns.join(","),
    ...rows.map((row) => row.map(escapeCsv).join(","))
  ].join("\r\n");

  const blob = new Blob(["\uFEFF", csv], {
    type: "text/csv;charset=utf-8"
  });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `impact-analysis-${detail.investigation.id}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ImpactAnalysisPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<InvestigationDetail | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<InvestigationFinding | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<FindingPriority | "">("");
  const [statusFilter, setStatusFilter] = useState<FindingStatus | "">("");
  const [typeFilter, setTypeFilter] = useState<FindingType | "">("");

  const loadInvestigations = useCallback(async () => {
    setLoadingList(true);
    setError("");

    try {
      const rows = await impactApi.listInvestigations({
        limit: 100,
        offset: 0
      });
      setInvestigations(rows);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    void loadInvestigations();
  }, [loadInvestigations]);

  const openInvestigation = useCallback(async (id: string) => {
    setLoadingDetail(true);
    setError("");

    try {
      const detail = await impactApi.getInvestigation(id);
      setSelectedDetail(detail);
      setPriorityFilter("");
      setStatusFilter("");
      setTypeFilter("");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  function handleCreated(detail: InvestigationDetail) {
    setShowCreate(false);
    setSelectedDetail(detail);
    setInvestigations((current) => [
      detail.investigation,
      ...current.filter((item) => item.id !== detail.investigation.id)
    ]);
  }

  function handleReviewSaved(updated: InvestigationFinding) {
    setSelectedFinding(null);
    setSelectedDetail((current) => {
      if (!current) return current;

      return {
        ...current,
        findings: current.findings.map((finding) =>
          finding.id === updated.id ? updated : finding
        )
      };
    });
  }

  const findings = selectedDetail?.findings ?? [];

  const filteredFindings = useMemo(() => {
    const normalized = search.trim().toLowerCase();

    return findings.filter((finding) => {
      if (priorityFilter && finding.priority !== priorityFilter) return false;
      if (statusFilter && finding.status !== statusFilter) return false;
      if (typeFilter && finding.finding_type !== typeFilter) return false;

      if (
        normalized &&
        !`${finding.title} ${finding.summary} ${finding.finding_type}`
          .toLowerCase()
          .includes(normalized)
      ) {
        return false;
      }

      return true;
    });
  }, [findings, search, priorityFilter, statusFilter, typeFilter]);

  const priorityCounts = useMemo(() => {
    const counts: Record<FindingPriority, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      informational: 0
    };

    findings.forEach((finding) => {
      counts[finding.priority] += 1;
    });

    return counts;
  }, [findings]);

  const openCount = findings.filter(
    (finding) => finding.status === "open"
  ).length;

  const reviewedCount = findings.filter(
    (finding) =>
      finding.status === "under_review" ||
      finding.status === "confirmed" ||
      finding.status === "dismissed"
  ).length;

  const evidenceCount = findings.reduce(
    (total, finding) => total + finding.evidence_ids.length,
    0
  );

  const visibleInvestigations = investigations;

  return (
    <div className="ia-page">
      <PageHeader
        eyebrow="GRAPH INTELLIGENCE"
        title="Impact Analysis & Reporting"
        description="Run graph-powered impact investigations, prioritize findings, and capture human review decisions."
        actions={
          <button
            className="ia-button primary"
            onClick={() => setShowCreate(true)}
          >
            <Plus size={16} />
            New investigation
          </button>
        }
      />

      {error && (
        <div className="ia-alert">
          <AlertCircle size={16} />
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Dismiss">
            <X size={15} />
          </button>
        </div>
      )}

      <div className="ia-layout">
        <aside className="ia-history-panel">
          <div className="ia-panel-heading">
            <div>
              <h2>Investigations</h2>
              <p>{investigations.length} recent records</p>
            </div>
            <button
              className="ia-icon-button"
              onClick={() => void loadInvestigations()}
              disabled={loadingList}
              aria-label="Refresh investigations"
            >
              {loadingList
                ? <LoaderCircle className="ia-spin" size={16} />
                : <RefreshCw size={16} />}
            </button>
          </div>

          <div className="ia-history-list">
            {loadingList ? (
              <div className="ia-empty">
                <LoaderCircle className="ia-spin" size={22} />
                Loading investigations...
              </div>
            ) : visibleInvestigations.length === 0 ? (
              <div className="ia-empty">
                <ClipboardList size={25} />
                <strong>No investigations yet</strong>
                <span>Create an investigation to analyze graph impact.</span>
              </div>
            ) : (
              visibleInvestigations.map((run) => (
                <button
                  key={run.id}
                  className={`ia-history-item ${selectedDetail?.investigation.id === run.id ? "active" : ""}`}
                  onClick={() => void openInvestigation(run.id)}
                >
                  <div className="ia-history-top">
                    <span className="ia-history-icon"><Activity size={15} /></span>
                    <RunStatus status={run.status} />
                  </div>
                  <strong>{run.title}</strong>
                  <span className="ia-history-description">
                    {run.description || run.summary || "No description provided."}
                  </span>
                  <small>{dateLabel(run.created_at)}</small>
                </button>
              ))
            )}
          </div>
        </aside>

        <main className="ia-main-panel">
          {loadingDetail && (
            <div className="ia-loading">
              <LoaderCircle className="ia-spin" size={25} />
              Loading investigation...
            </div>
          )}

          {!selectedDetail && !loadingDetail ? (
            <div className="ia-welcome">
              <div className="ia-welcome-icon"><FileSearch size={29} /></div>
              <h2>Understand the impact across your graph</h2>
              <p>
                Select an existing investigation or create a new one using entities
                from the Knowledge Graph.
              </p>
              <button className="ia-button primary" onClick={() => setShowCreate(true)}>
                <Plus size={16} />
                Create investigation
              </button>
            </div>
          ) : selectedDetail ? (
            <>
              <div className="ia-detail-header">
                <div>
                  <span className="ia-eyebrow">INVESTIGATION REPORT</span>
                  <h2>{selectedDetail.investigation.title}</h2>
                  <p>{selectedDetail.investigation.description || "No description provided."}</p>
                  <div className="ia-detail-meta">
                    <RunStatus status={selectedDetail.investigation.status} />
                    <span>Depth {selectedDetail.investigation.depth}</span>
                    <span>{dateLabel(selectedDetail.investigation.created_at)}</span>
                  </div>
                </div>
                <button
                  className="ia-button secondary"
                  onClick={() => exportFindings(selectedDetail)}
                  disabled={findings.length === 0}
                >
                  <ArrowDownToLine size={15} />
                  Export CSV
                </button>
              </div>

              <div className="ia-summary-grid">
                <div className="ia-summary-card">
                  <span>Total findings</span>
                  <strong>{findings.length}</strong>
                  <small>Generated by this investigation</small>
                </div>
                <div className="ia-summary-card">
                  <span>Open findings</span>
                  <strong>{openCount}</strong>
                  <small>Awaiting review</small>
                </div>
                <div className="ia-summary-card">
                  <span>Reviewed findings</span>
                  <strong>{reviewedCount}</strong>
                  <small>Review workflow status</small>
                </div>
                <div className="ia-summary-card">
                  <span>Evidence references</span>
                  <strong>{evidenceCount}</strong>
                  <small>Linked evidence IDs</small>
                </div>
              </div>

              <section className="ia-priority-panel">
                <div className="ia-section-heading">
                  <div>
                    <h3>Priority distribution</h3>
                    <p>Backend-generated triage scores grouped by priority.</p>
                  </div>
                  <Activity size={17} />
                </div>

                <div className="ia-priority-bars">
                  {PRIORITY_ORDER.map((priority) => {
                    const count = priorityCounts[priority];
                    const width = findings.length
                      ? (count / findings.length) * 100
                      : 0;

                    return (
                      <div className="ia-priority-row" key={priority}>
                        <span>{titleCase(priority)}</span>
                        <div className="ia-priority-track">
                          <div
                            className={`ia-priority-fill ${priority}`}
                            style={{ width: `${width}%` }}
                          />
                        </div>
                        <strong>{count}</strong>
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="ia-findings-panel">
                <div className="ia-section-heading">
                  <div>
                    <h3>Impact findings</h3>
                    <p>{filteredFindings.length} of {findings.length} findings displayed.</p>
                  </div>
                  <span className="ia-findings-total">
                    {findings.length} total
                  </span>
                </div>

                <div className="ia-finding-filters">
                  <div className="ia-finding-search">
                    <Search size={15} />
                    <input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Search findings..."
                    />
                  </div>

                  <select
                    value={priorityFilter}
                    onChange={(event) =>
                      setPriorityFilter(event.target.value as FindingPriority | "")
                    }
                    aria-label="Filter by priority"
                  >
                    <option value="">All priorities</option>
                    {PRIORITY_ORDER.map((item) => (
                      <option key={item} value={item}>{titleCase(item)}</option>
                    ))}
                  </select>

                  <select
                    value={statusFilter}
                    onChange={(event) =>
                      setStatusFilter(event.target.value as FindingStatus | "")
                    }
                    aria-label="Filter by review status"
                  >
                    <option value="">All statuses</option>
                    <option value="open">Open</option>
                    <option value="under_review">Under review</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="dismissed">Dismissed</option>
                  </select>

                  <select
                    value={typeFilter}
                    onChange={(event) =>
                      setTypeFilter(event.target.value as FindingType | "")
                    }
                    aria-label="Filter by finding type"
                  >
                    <option value="">All finding types</option>
                    {FINDING_TYPES.map((item) => (
                      <option key={item} value={item}>
                        {FINDING_TYPE_LABELS[item]}
                      </option>
                    ))}
                  </select>
                </div>

                {filteredFindings.length === 0 ? (
                  <div className="ia-empty ia-no-findings">
                    <CircleAlert size={25} />
                    <strong>No findings match these filters</strong>
                    <span>Change or clear the filters to see more results.</span>
                  </div>
                ) : (
                  <div className="ia-findings-list">
                    {filteredFindings.map((finding) => (
                      <article className="ia-finding-card" key={finding.id}>
                        <div className="ia-finding-main">
                          <div className="ia-finding-topline">
                            <span className="ia-finding-type">
                              {FINDING_TYPE_LABELS[finding.finding_type]}
                            </span>
                            <PriorityBadge priority={finding.priority} />
                            <FindingStatusBadge status={finding.status} />
                          </div>

                          <h4>{finding.title}</h4>
                          <p>{finding.summary}</p>

                          <div className="ia-finding-meta">
                            <span>Score: <strong>{Number(finding.priority_score).toFixed(2)}</strong></span>
                            <span>
                              Confidence: <strong>
                                {finding.confidence == null
                                  ? "Not provided"
                                  : `${(Number(finding.confidence) * 100).toFixed(0)}%`}
                              </strong>
                            </span>
                            <span>Path nodes: <strong>{finding.path_node_ids.length}</strong></span>
                            <span>Evidence: <strong>{finding.evidence_ids.length}</strong></span>
                          </div>

                          {finding.review_decision && (
                            <div className="ia-decision-line">
                              Decision: {REVIEW_DECISION_LABELS[finding.review_decision]}
                            </div>
                          )}
                        </div>

                        <div className="ia-finding-actions">
                          <button
                            className="ia-button secondary"
                            onClick={() => setSelectedFinding(finding)}
                          >
                            <ShieldCheck size={14} />
                            Review
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <section className="ia-report-notes">
                <div className="ia-section-heading">
                  <div>
                    <h3>Investigation summary</h3>
                    <p>Summary returned by the graph-investigation service.</p>
                  </div>
                  <ClipboardList size={17} />
                </div>
                <p>
                  {selectedDetail.investigation.summary ||
                    "The backend did not provide a summary for this investigation."}
                </p>

                <details>
                  <summary>Technical result metadata</summary>
                  <pre>{JSON.stringify(
                    selectedDetail.investigation.result_metadata,
                    null,
                    2
                  )}</pre>
                </details>
              </section>

              <div className="ia-disclaimer">
                <ShieldCheck size={16} />
                <span>
                  Findings and scores are decision-support outputs. Applicability,
                  compliance, and legal conclusions require qualified human review
                  of the original sources and evidence.
                </span>
              </div>
            </>
          ) : null}
        </main>
      </div>

      {showCreate && (
        <CreateInvestigationPanel
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}

      {selectedFinding && (
        <FindingReviewPanel
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
          onSaved={handleReviewSaved}
        />
      )}
    </div>
  );
}
