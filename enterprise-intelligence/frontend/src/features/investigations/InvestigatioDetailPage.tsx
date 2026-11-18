
import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleHelp,
  FileText,
  LoaderCircle,
  Play,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  XCircle
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { getApiErrorMessage } from "../../lib/api";

import {
  executeInvestigation,
  getInvestigation,
  reviewInvestigation,
  type ClaimVerification,
  type InvestigationDetail,
  type InvestigationReport,
  type ReviewDecision
} from "./investigations-api";

function statusAppearance(status: string) {
  if (["approved", "supported"].includes(status)) return "success" as const;
  if (["review_required", "insufficient", "uncertain"].includes(status)) {
    return "warning" as const;
  }
  if (["failed", "rejected", "contradicted"].includes(status)) {
    return "danger" as const;
  }
  if (["queued", "planning", "researching", "analyzing", "comparing", "verifying"].includes(status)) {
    return "info" as const;
  }
  return "neutral" as const;
}

function formatStatus(value: string) {
  return value.replaceAll("_", " ");
}

function dateLabel(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function EvidenceReferences({
  ids
}: {
  ids: string[];
}) {
  if (ids.length === 0) {
    return <span className="f5-muted">No evidence references supplied</span>;
  }

  return (
    <div className="f5-chip-list">
      {ids.map((id) => (
        <span className="f5-chip" key={id}>{id}</span>
      ))}
    </div>
  );
}

function ClaimVerdictCard({
  verification,
  claims
}: {
  verification: ClaimVerification;
  claims: InvestigationReport["intelligence"] extends infer T
    ? T extends { claims: infer C } ? C : never
    : never;
}) {
  const claim = Array.isArray(claims)
    ? claims.find((item: any) => item.claim_id === verification.claim_id)
    : undefined;

  return (
    <article className="f5-verification-card">
      <div className="f5-verification-top">
        <div>
          <span className="f5-small-label">CLAIM {verification.claim_id}</span>
          <h4>{claim?.text ?? "Claim text not available in the report"}</h4>
        </div>

        <StatusBadge status={statusAppearance(verification.verdict)}>
          {verification.verdict}
        </StatusBadge>
      </div>

      <p className="f5-rationale">{verification.rationale}</p>

      <div className="f5-evidence-columns">
        <div>
          <span className="f5-evidence-label f5-positive">
            Supporting evidence
          </span>
          <EvidenceReferences ids={verification.supporting_evidence_ids} />
        </div>

        <div>
          <span className="f5-evidence-label f5-negative">
            Contradicting evidence
          </span>
          <EvidenceReferences ids={verification.contradicting_evidence_ids} />
        </div>
      </div>

      {verification.limitations.length > 0 && (
        <ul className="f5-inline-limitations">
          {verification.limitations.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
    </article>
  );
}

export function InvestigationDetailPage() {
  const { investigationId } = useParams();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [comments, setComments] = useState("");
  const [activeTab, setActiveTab] = useState<
    "findings" | "verification" | "evidence" | "events"
  >("findings");
  const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);

  const loadDetail = useCallback(async (refresh = false) => {
    if (!investigationId) return;

    if (refresh) setRefreshing(true);
    else setLoading(true);

    setError("");

    try {
      const result = await getInvestigation(investigationId);
      setDetail(result);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [investigationId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  async function handleExecute() {
    if (!investigationId) return;

    setExecuting(true);
    setError("");

    try {
      await executeInvestigation(investigationId, false);
      await loadDetail(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
      await loadDetail(true);
    } finally {
      setExecuting(false);
    }
  }

  async function handleReview(decision: ReviewDecision) {
    if (!investigationId || !detail?.latest_run) return;

    if (
      decision !== "approve" &&
      comments.trim().length === 0
    ) {
      setReviewError("Add a review comment before rejecting or requesting changes.");
      return;
    }

    setReviewing(true);
    setReviewError("");

    try {
      await reviewInvestigation(
        investigationId,
        detail.latest_run.id,
        {
          decision,
          comments: comments.trim()
        }
      );

      setComments("");
      await loadDetail(true);
    } catch (err) {
      setReviewError(getApiErrorMessage(err));
    } finally {
      setReviewing(false);
    }
  }

  if (loading) {
    return (
      <div className="f5-loading f5-page-loading">
        <LoaderCircle size={26} className="f5-spin" />
        <span>Loading investigation...</span>
      </div>
    );
  }

  if (error && !detail) {
    return (
      <div className="f5-page">
        <div className="f5-alert f5-alert-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
        <button
          type="button"
          className="f5-secondary-button"
          onClick={() => navigate("/investigations")}
        >
          <ArrowLeft size={15} />
          Back to investigations
        </button>
      </div>
    );
  }

  if (!detail) return null;

  const investigation = detail.investigation;
  const run = detail.latest_run;
  const report = (run?.result ?? {}) as InvestigationReport;
  const intelligence = report.intelligence;
  const findings = report.findings ?? [];
  const evidence = report.evidence ?? [];
  const issues = report.verification_issues ?? [];
  const comparisons = report.comparisons ?? [];
  const verifications = intelligence?.verifications ?? [];
  const contradictions = intelligence?.contradictions ?? [];
  const confidence = intelligence?.confidence ?? [];
  const sourceQuality = intelligence?.source_quality ?? [];
  const applicability = intelligence?.applicability ?? [];
  const limitations = report.limitations ?? [];

  const canExecute =
    ["draft", "failed", "approved", "rejected"].includes(investigation.status);

  const canReview =
    run?.status === "review_required" &&
    investigation.status === "review_required";

  const summary = intelligence?.summary;

  return (
    <div className="f5-page">
      <div className="f5-back-row">
        <Link to="/investigations" className="f5-back-link">
          <ArrowLeft size={15} />
          All investigations
        </Link>

        <button
          type="button"
          className="f5-icon-button"
          onClick={() => void loadDetail(true)}
          disabled={refreshing}
          aria-label="Refresh investigation"
        >
          {refreshing ? (
            <LoaderCircle size={16} className="f5-spin" />
          ) : (
            <RefreshCw size={16} />
          )}
        </button>
      </div>

      <PageHeader
        eyebrow="INVESTIGATION WORKSPACE"
        title={investigation.title}
        description={investigation.question}
        actions={
          canExecute ? (
            <button
              type="button"
              className="f5-primary-button"
              onClick={handleExecute}
              disabled={executing}
            >
              {executing ? (
                <LoaderCircle size={16} className="f5-spin" />
              ) : (
                <Play size={15} />
              )}
              {executing ? "Executing workflow..." : "Execute investigation"}
            </button>
          ) : undefined
        }
      />

      {error && (
        <div className="f5-alert f5-alert-error" role="alert">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
      )}

      <section className="f5-detail-summary">
        <div>
          <span className="f5-small-label">INVESTIGATION STATUS</span>
          <StatusBadge status={statusAppearance(investigation.status)}>
            {formatStatus(investigation.status)}
          </StatusBadge>
        </div>

        <div>
          <span className="f5-small-label">CREATED</span>
          <strong>{dateLabel(investigation.created_at)}</strong>
        </div>

        <div>
          <span className="f5-small-label">LATEST RUN</span>
          <strong>{run ? dateLabel(run.created_at) : "Not executed"}</strong>
        </div>

        <div>
          <span className="f5-small-label">RUN STATUS</span>
          <strong>{run ? formatStatus(run.status) : "—"}</strong>
        </div>
      </section>

      <section className="f5-scope-panel">
        <div className="f5-panel-heading">
          <div>
            <h2>Investigation scope</h2>
            <p>Scope values saved with the investigation request.</p>
          </div>
        </div>

        <div className="f5-scope-grid">
          {Object.entries(investigation.scope ?? {})
            .filter(([key]) => key !== "document_ids")
            .map(([key, value]) => (
              <div className="f5-scope-item" key={key}>
                <span>{formatStatus(key)}</span>
                <strong>{String(value ?? "—")}</strong>
              </div>
            ))}

          <div className="f5-scope-item">
            <span>Selected documents</span>
            <strong>
              {asStringArray(investigation.scope?.document_ids).length}
            </strong>
          </div>
        </div>
      </section>

      {run && (
        <section className="f5-result-overview">
          <div className="f5-panel-heading">
            <div>
              <h2>Investigation results</h2>
              <p>
                Results from the latest completed workflow run.
              </p>
            </div>
            <StatusBadge status={statusAppearance(run.status)}>
              {formatStatus(run.status)}
            </StatusBadge>
          </div>

          <div className="f5-result-metrics">
            <div>
              <strong>{findings.length}</strong>
              <span>Findings</span>
            </div>
            <div>
              <strong>{evidence.length}</strong>
              <span>Evidence passages</span>
            </div>
            <div>
              <strong>{issues.length}</strong>
              <span>Verification issues</span>
            </div>
            <div>
              <strong>{verifications.length}</strong>
              <span>Verified claims</span>
            </div>
            <div>
              <strong>{contradictions.length}</strong>
              <span>Contradictions</span>
            </div>
          </div>

          {report.summary && (
            <div className="f5-executive-summary">
              <span className="f5-small-label">INVESTIGATION SUMMARY</span>
              <p>{report.summary}</p>
            </div>
          )}

          {summary && (
            <div className="f5-claim-summary">
              <div>
                <span>Supported</span>
                <strong>{summary.supported_claims}</strong>
              </div>
              <div>
                <span>Contradicted</span>
                <strong>{summary.contradicted_claims}</strong>
              </div>
              <div>
                <span>Insufficient</span>
                <strong>{summary.insufficient_claims}</strong>
              </div>
              <div>
                <span>Uncertain applicability</span>
                <strong>{summary.uncertain_applicability}</strong>
              </div>
            </div>
          )}
        </section>
      )}

      {run && (
        <section className="f5-panel f5-results-panel">
          <div className="f5-tabs" role="tablist" aria-label="Investigation results">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "findings"}
              className={activeTab === "findings" ? "active" : ""}
              onClick={() => setActiveTab("findings")}
            >
              Findings ({findings.length})
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "verification"}
              className={activeTab === "verification" ? "active" : ""}
              onClick={() => setActiveTab("verification")}
            >
              Verification ({verifications.length + issues.length})
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "evidence"}
              className={activeTab === "evidence" ? "active" : ""}
              onClick={() => setActiveTab("evidence")}
            >
              Evidence ({evidence.length})
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "events"}
              className={activeTab === "events" ? "active" : ""}
              onClick={() => setActiveTab("events")}
            >
              Run history ({detail.events.length})
            </button>
          </div>

          {activeTab === "findings" && (
            <div className="f5-tab-content">
              {findings.length === 0 ? (
                <div className="f5-inline-empty">
                  No findings were returned by this run.
                </div>
              ) : (
                <div className="f5-finding-list">
                  {findings.map((finding) => (
                    <article className="f5-finding-card" key={finding.finding_id}>
                      <div className="f5-finding-heading">
                        <div>
                          <span className="f5-small-label">
                            {finding.category} · {finding.finding_id}
                          </span>
                          <h3>{finding.statement}</h3>
                        </div>

                        <StatusBadge
                          status={
                            finding.review_required ? "warning" : "info"
                          }
                        >
                          {finding.review_required
                            ? "Review required"
                            : finding.confidence_label}
                        </StatusBadge>
                      </div>

                      <EvidenceReferences ids={finding.evidence_ids} />
                    </article>
                  ))}
                </div>
              )}

              {comparisons.length > 0 && (
                <div className="f5-subsection">
                  <h3>Finding comparisons</h3>
                  {comparisons.map((comparison, index) => (
                    <pre className="f5-json-block" key={index}>
                      {JSON.stringify(comparison, null, 2)}
                    </pre>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "verification" && (
            <div className="f5-tab-content">
              {issues.length > 0 && (
                <div className="f5-subsection">
                  <h3>Investigation verification issues</h3>

                  {issues.map((issue, index) => (
                    <article className="f5-issue-card" key={index}>
                      <div className="f5-issue-icon">
                        <ShieldAlert size={17} />
                      </div>
                      <div>
                        <strong>{formatStatus(issue.issue_type)}</strong>
                        <p>{issue.description}</p>
                        {issue.finding_id && (
                          <small>Finding: {issue.finding_id}</small>
                        )}
                        <EvidenceReferences ids={issue.evidence_ids} />
                      </div>
                    </article>
                  ))}
                </div>
              )}

              <div className="f5-subsection">
                <h3>M5 claim verification</h3>

                {verifications.length === 0 ? (
                  <div className="f5-inline-empty">
                    No claim-verification results were returned.
                  </div>
                ) : (
                  verifications.map((verification) => (
                    <ClaimVerdictCard
                      key={verification.claim_id}
                      verification={verification}
                      claims={intelligence?.claims ?? []}
                    />
                  ))
                )}
              </div>

              {contradictions.length > 0 && (
                <div className="f5-subsection">
                  <h3>Contradictions detected</h3>

                  {contradictions.map((item) => (
                    <article className="f5-contradiction-card" key={item.contradiction_id}>
                      <div className="f5-verification-top">
                        <strong>{item.contradiction_id}</strong>
                        <StatusBadge status={statusAppearance(item.severity)}>
                          {item.severity} severity
                        </StatusBadge>
                      </div>

                      <p>{item.description}</p>
                      <small>
                        Claims: {item.claim_a_id} and {item.claim_b_id}
                      </small>
                      <EvidenceReferences ids={item.evidence_ids} />
                    </article>
                  ))}
                </div>
              )}

              {applicability.length > 0 && (
                <div className="f5-subsection">
                  <h3>Regulatory applicability</h3>
                  <div className="f5-simple-list">
                    {applicability.map((item: any, index: number) => (
                      <article key={`${item.claim_id}-${index}`}>
                        <div>
                          <strong>{item.claim_id}</strong>
                          <StatusBadge status={statusAppearance(item.verdict)}>
                            {item.verdict}
                          </StatusBadge>
                        </div>
                        <p>{item.rationale}</p>
                        {item.missing_scope_information?.length > 0 && (
                          <small>
                            Missing scope information:{" "}
                            {item.missing_scope_information.join(", ")}
                          </small>
                        )}
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {confidence.length > 0 && (
                <div className="f5-subsection">
                  <h3>Claim confidence signals</h3>
                  <div className="f5-simple-list">
                    {confidence.map((item: any, index: number) => (
                      <article key={`${item.claim_id}-${index}`}>
                        <div>
                          <strong>{item.claim_id}</strong>
                          <StatusBadge status={statusAppearance(item.label)}>
                            {item.label}
                          </StatusBadge>
                        </div>
                        <p>{item.explanation}</p>
                        <small>
                          Score:{" "}
                          {typeof item.score === "number"
                            ? item.score.toFixed(4)
                            : "Not available"}
                        </small>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {sourceQuality.length > 0 && (
                <div className="f5-subsection">
                  <h3>Source quality and provenance</h3>
                  <div className="f5-source-grid">
                    {sourceQuality.map((source: any, index: number) => (
                      <article key={`${source.document_id}-${index}`}>
                        <strong>{source.document_title}</strong>
                        <span>
                          Quality score:{" "}
                          {typeof source.quality_score === "number"
                            ? source.quality_score.toFixed(3)
                            : "Not available"}
                        </span>
                        <span>Authority: {source.authority_level}</span>
                        <span>
                          Provenance:{" "}
                          {typeof source.provenance_score === "number"
                            ? source.provenance_score.toFixed(3)
                            : "Not available"}
                        </span>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {limitations.length > 0 && (
                <div className="f5-limitations">
                  <div>
                    <CircleHelp size={17} />
                    <strong>Limitations and review notes</strong>
                  </div>
                  <ul>
                    {limitations.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {activeTab === "evidence" && (
            <div className="f5-tab-content">
              {evidence.length === 0 ? (
                <div className="f5-inline-empty">
                  No evidence passages were returned.
                </div>
              ) : (
                <div className="f5-evidence-list">
                  {evidence.map((item) => {
                    const expanded = expandedEvidence === item.evidence_id;

                    return (
                      <article className="f5-evidence-card" key={item.evidence_id}>
                        <button
                          type="button"
                          className="f5-evidence-toggle"
                          onClick={() =>
                            setExpandedEvidence(
                              expanded ? null : item.evidence_id
                            )
                          }
                        >
                          <div className="f5-evidence-title">
                            <span className="f5-evidence-file-icon">
                              <FileText size={17} />
                            </span>
                            <span>
                              <strong>{item.document_title}</strong>
                              <small>
                                {item.evidence_id}
                                {" · "}
                                Version {item.version_number}
                                {" · "}
                                Pages {item.page_start}–{item.page_end}
                              </small>
                            </span>
                          </div>

                          {expanded ? (
                            <ChevronUp size={17} />
                          ) : (
                            <ChevronDown size={17} />
                          )}
                        </button>

                        {expanded && (
                          <div className="f5-evidence-expanded">
                            <p>{item.content}</p>
                            <div className="f5-evidence-footer">
                              <span>Document ID: {item.document_id}</span>
                              <span>Chunk ID: {item.chunk_id}</span>
                              <span>
                                Retrieval score:{" "}
                                {typeof item.retrieval_score === "number"
                                  ? item.retrieval_score.toFixed(5)
                                  : "Not available"}
                              </span>
                            </div>
                            <Link
                              to={`/documents/${item.document_id}`}
                              className="f5-document-link"
                            >
                              Open source document
                            </Link>
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === "events" && (
            <div className="f5-tab-content">
              {detail.events.length === 0 ? (
                <div className="f5-inline-empty">
                  No run events have been recorded.
                </div>
              ) : (
                <div className="f5-timeline">
                  {detail.events.map((event) => (
                    <article className="f5-timeline-item" key={event.id}>
                      <div className="f5-timeline-dot" />
                      <div>
                        <span className="f5-small-label">
                          {dateLabel(event.created_at)}
                        </span>
                        <h4>{formatStatus(event.event_type)}</h4>
                        <p>{event.description}</p>
                        {Object.keys(event.payload ?? {}).length > 0 && (
                          <details>
                            <summary>Event details</summary>
                            <pre className="f5-json-block">
                              {JSON.stringify(event.payload, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {!run && (
        <section className="f5-panel f5-no-run">
          <div className="f5-empty-icon">
            <Play size={23} />
          </div>
          <h3>This investigation has not been executed</h3>
          <p>
            The investigation has been saved. Execute it to start planning,
            evidence retrieval, analysis and verification.
          </p>
          {canExecute && (
            <button
              type="button"
              className="f5-primary-button"
              onClick={handleExecute}
              disabled={executing}
            >
              {executing ? (
                <LoaderCircle size={16} className="f5-spin" />
              ) : (
                <Play size={15} />
              )}
              {executing ? "Executing..." : "Execute investigation"}
            </button>
          )}
        </section>
      )}

      {run?.status === "failed" && (
        <div className="f5-alert f5-alert-error">
          <XCircle size={17} />
          <div>
            <strong>Investigation execution failed</strong>
            <p>{run.error_message ?? "The backend did not provide an error message."}</p>
          </div>
        </div>
      )}

      {canReview && (
        <section className="f5-review-panel">
          <div className="f5-review-heading">
            <div className="f5-review-icon">
              <ShieldCheck size={21} />
            </div>
            <div>
              <h2>Human review required</h2>
              <p>
                Review the findings, source evidence, contradictions,
                confidence signals and limitations before making a decision.
              </p>
            </div>
          </div>

          {reviewError && (
            <div className="f5-alert f5-alert-error" role="alert">
              <AlertCircle size={16} />
              <span>{reviewError}</span>
            </div>
          )}

          <label className="f5-field">
            <span>Reviewer comments</span>
            <textarea
              value={comments}
              onChange={(event) => setComments(event.target.value)}
              maxLength={5000}
              rows={3}
              placeholder="Add reasoning, requested corrections or approval notes..."
            />
          </label>

          <div className="f5-review-actions">
            <button
              type="button"
              className="f5-danger-button"
              onClick={() => void handleReview("reject")}
              disabled={reviewing}
            >
              <XCircle size={16} />
              Reject
            </button>

            <button
              type="button"
              className="f5-secondary-button"
              onClick={() => void handleReview("request_changes")}
              disabled={reviewing}
            >
              <RefreshCw size={15} />
              Request changes
            </button>

            <button
              type="button"
              className="f5-approve-button"
              onClick={() => void handleReview("approve")}
              disabled={reviewing}
            >
              {reviewing ? (
                <LoaderCircle size={16} className="f5-spin" />
              ) : (
                <CheckCircle2 size={16} />
              )}
              Approve investigation
            </button>
          </div>
        </section>
      )}

      {investigation.status === "approved" && (
        <div className="f5-final-state f5-final-approved">
          <CheckCircle2 size={18} />
          This investigation has been approved.
        </div>
      )}

      {investigation.status === "rejected" && (
        <div className="f5-final-state f5-final-rejected">
          <XCircle size={18} />
          This investigation has been rejected.
        </div>
      )}
    </div>
  );
}
