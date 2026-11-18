
import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FileText,
  LoaderCircle,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  XCircle
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { getApiErrorMessage } from "../../lib/api";

import {
  getPublicationVersions,
  getRegulatoryAlert,
  reviewRegulatoryAlert,
  type ApplicabilityDecision,
  type RegulatoryAlertDetail,
  type RegulatoryPublicationVersion
} from "./regulatory-api";

function dateLabel(value?: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString();
}

function readable(value: string) {
  return value.replaceAll("_", " ");
}

function severityAppearance(severity: string) {
  if (severity === "high") return "danger" as const;
  if (severity === "medium") return "warning" as const;
  if (severity === "low") return "info" as const;
  return "neutral" as const;
}

function statusAppearance(status: string) {
  if (status === "reviewed") return "success" as const;
  if (status === "dismissed") return "neutral" as const;
  return "warning" as const;
}

function stringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function RegulatoryAlertDetailPage() {
  const { alertId } = useParams();

  const [detail, setDetail] = useState<RegulatoryAlertDetail | null>(null);
  const [versions, setVersions] = useState<
    RegulatoryPublicationVersion[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [success, setSuccess] = useState("");

  const [reviewStatus, setReviewStatus] = useState<
    "reviewed" | "dismissed"
  >("reviewed");

  const [applicability, setApplicability] = useState<
    ApplicabilityDecision | ""
  >("");

  const [effectiveAt, setEffectiveAt] = useState("");
  const [notes, setNotes] = useState("");

  const loadDetail = useCallback(async (refresh = false) => {
    if (!alertId) return;

    if (refresh) setRefreshing(true);
    else setLoading(true);

    setError("");

    try {
      const result = await getRegulatoryAlert(alertId);
      setDetail(result);

      const versionData = await getPublicationVersions(
        result.publication.id
      );

      setVersions(versionData);

      setReviewStatus(
        result.alert.status === "dismissed" ? "dismissed" : "reviewed"
      );

      setApplicability(
        result.alert.relevance_status === "applicable" ||
        result.alert.relevance_status === "not_applicable" ||
        result.alert.relevance_status === "uncertain"
          ? result.alert.relevance_status
          : ""
      );

      setEffectiveAt(
        result.publication.effective_at
          ? result.publication.effective_at.slice(0, 10)
          : ""
      );

      setNotes(result.alert.review_notes ?? "");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [alertId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  async function handleReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!alertId || !detail) return;

    setSaving(true);
    setReviewError("");
    setSuccess("");

    try {
      await reviewRegulatoryAlert(alertId, {
        status: reviewStatus,
        notes: notes.trim() || null,
        applicability_decision: applicability || null,
        effective_at: effectiveAt
          ? new Date(`${effectiveAt}T00:00:00`).toISOString()
          : null
      });

      setSuccess(
        reviewStatus === "reviewed"
          ? "Regulatory alert marked as reviewed."
          : "Regulatory alert dismissed."
      );

      await loadDetail(true);
    } catch (err) {
      setReviewError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="f6-loading f6-page-loading">
        <LoaderCircle size={25} className="f6-spin" />
        Loading regulatory alert...
      </div>
    );
  }

  if (error && !detail) {
    return (
      <div className="f6-page">
        <div className="f6-alert f6-alert-error" role="alert">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
        <Link to="/regulatory" className="f6-secondary-button">
          <ArrowLeft size={15} />
          Back to regulatory monitoring
        </Link>
      </div>
    );
  }

  if (!detail) return null;

  const { alert, publication, version } = detail;
  const diff = version.diff_summary ?? {};
  const addedExcerpt = stringList(diff.added_excerpt);
  const removedExcerpt = stringList(diff.removed_excerpt);
  const limitations = stringList(diff.limitations);

  const isPending = alert.status === "pending";

  return (
    <div className="f6-page">
      <div className="f6-back-row">
        <Link to="/regulatory" className="f6-back-link">
          <ArrowLeft size={15} />
          Regulatory monitoring
        </Link>

        <button
          type="button"
          className="f6-icon-button"
          onClick={() => void loadDetail(true)}
          disabled={refreshing}
          aria-label="Refresh alert"
        >
          {refreshing ? (
            <LoaderCircle size={16} className="f6-spin" />
          ) : (
            <RefreshCw size={16} />
          )}
        </button>
      </div>

      <PageHeader
        eyebrow="REGULATORY ALERT REVIEW"
        title={alert.title}
        description={alert.summary}
        actions={
          <div className="f6-detail-badges">
            <StatusBadge status={severityAppearance(alert.severity)}>
              {alert.severity}
            </StatusBadge>
            <StatusBadge status={statusAppearance(alert.status)}>
              {readable(alert.status)}
            </StatusBadge>
          </div>
        }
      />

      {error && (
        <div className="f6-alert f6-alert-error" role="alert">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="f6-alert f6-alert-success" role="status">
          <CheckCircle2 size={17} />
          <span>{success}</span>
        </div>
      )}

      <section className="f6-detail-grid">
        <article className="f6-detail-card">
          <span className="f6-small-label">ALERT TYPE</span>
          <strong>{readable(alert.alert_type)}</strong>
        </article>

        <article className="f6-detail-card">
          <span className="f6-small-label">RELEVANCE SCREENING</span>
          <strong>{readable(alert.relevance_status)}</strong>
        </article>

        <article className="f6-detail-card">
          <span className="f6-small-label">CURRENT VERSION</span>
          <strong>Version {publication.current_version_number}</strong>
        </article>

        <article className="f6-detail-card">
          <span className="f6-small-label">ALERT CREATED</span>
          <strong>{dateLabel(alert.created_at)}</strong>
        </article>
      </section>

      <div className="f6-detail-layout">
        <div className="f6-detail-main">
          <section className="f6-panel">
            <div className="f6-section-toolbar">
              <div>
                <h2>Publication information</h2>
                <p>Publication metadata returned by the monitoring service.</p>
              </div>
              <FileText size={19} className="f6-heading-icon" />
            </div>

            <div className="f6-publication-grid">
              <div>
                <span>Publication title</span>
                <strong>{publication.title}</strong>
              </div>

              <div>
                <span>Published date</span>
                <strong>{dateLabel(publication.published_at)}</strong>
              </div>

              <div>
                <span>Effective date</span>
                <strong>{dateLabel(publication.effective_at)}</strong>
              </div>

              <div>
                <span>Current version number</span>
                <strong>{publication.current_version_number}</strong>
              </div>

              <div>
                <span>Observed version</span>
                <strong>{version.version_number}</strong>
              </div>

              <div>
                <span>Observed at</span>
                <strong>{dateLabel(version.observed_at)}</strong>
              </div>
            </div>

            <a
              href={publication.canonical_url}
              target="_blank"
              rel="noopener noreferrer"
              className="f6-external-link"
            >
              Open official publication
              <ExternalLink size={14} />
            </a>
          </section>

          <section className="f6-panel">
            <div className="f6-section-toolbar">
              <div>
                <h2>Publication change comparison</h2>
                <p>
                  Textual difference summary for the observed publication
                  version.
                </p>
              </div>
              <StatusBadge status={diff.changed ? "warning" : "neutral"}>
                {diff.changed ? "Text changed" : "No text change reported"}
              </StatusBadge>
            </div>

            <div className="f6-diff-metrics">
              <div>
                <span>Previous lines</span>
                <strong>
                  {typeof diff.previous_line_count === "number"
                    ? diff.previous_line_count
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Current lines</span>
                <strong>
                  {typeof diff.current_line_count === "number"
                    ? diff.current_line_count
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Added lines</span>
                <strong className="f6-added-text">
                  {typeof diff.added_line_count === "number"
                    ? diff.added_line_count
                    : "—"}
                </strong>
              </div>

              <div>
                <span>Removed lines</span>
                <strong className="f6-removed-text">
                  {typeof diff.removed_line_count === "number"
                    ? diff.removed_line_count
                    : "—"}
                </strong>
              </div>
            </div>

            {addedExcerpt.length > 0 && (
              <div className="f6-diff-section">
                <h3 className="f6-added-text">Added text excerpts</h3>
                <pre className="f6-diff-block f6-added-block">
                  {addedExcerpt.join("\n")}
                </pre>
              </div>
            )}

            {removedExcerpt.length > 0 && (
              <div className="f6-diff-section">
                <h3 className="f6-removed-text">Removed text excerpts</h3>
                <pre className="f6-diff-block f6-removed-block">
                  {removedExcerpt.join("\n")}
                </pre>
              </div>
            )}

            {addedExcerpt.length === 0 &&
              removedExcerpt.length === 0 && (
                <div className="f6-inline-empty">
                  No text excerpts were supplied for this version.
                </div>
              )}

            {limitations.length > 0 && (
              <div className="f6-diff-limitations">
                <div>
                  <ShieldAlert size={16} />
                  <strong>Comparison limitations</strong>
                </div>
                <ul>
                  {limitations.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="f6-hash-row">
              <span>SHA-256 content hash</span>
              <code>{version.content_hash}</code>
            </div>
          </section>

          <section className="f6-panel">
            <div className="f6-section-toolbar">
              <div>
                <h2>Publication version history</h2>
                <p>Immutable versions recorded by the monitoring service.</p>
              </div>
              <span className="f6-version-count">
                {versions.length} versions
              </span>
            </div>

            {versions.length === 0 ? (
              <div className="f6-inline-empty">
                No publication versions were returned.
              </div>
            ) : (
              <div className="f6-version-list">
                {versions.map((item) => (
                  <article
                    className={`f6-version-item ${
                      item.id === version.id ? "current" : ""
                    }`}
                    key={item.id}
                  >
                    <div className="f6-version-number">
                      V{item.version_number}
                    </div>

                    <div className="f6-version-content">
                      <div>
                        <strong>Version {item.version_number}</strong>
                        {item.id === version.id && (
                          <StatusBadge status="info">Current alert version</StatusBadge>
                        )}
                      </div>
                      <span>{dateLabel(item.observed_at)}</span>
                      <code>{item.content_hash}</code>
                    </div>

                    <div className="f6-version-change">
                      {typeof item.diff_summary?.added_line_count === "number"
                        ? `+${item.diff_summary.added_line_count}`
                        : "—"}
                      {" / "}
                      {typeof item.diff_summary?.removed_line_count === "number"
                        ? `-${item.diff_summary.removed_line_count}`
                        : "—"}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="f6-panel">
            <div className="f6-section-toolbar">
              <div>
                <h2>Relevance screening evidence</h2>
                <p>
                  Terms matched against the publication during subscription
                  screening.
                </p>
              </div>
            </div>

            {alert.matched_terms.length === 0 ? (
              <div className="f6-inline-empty">
                No matched terms were recorded. The alert may have been
                created for manual triage because no organization filters
                were configured.
              </div>
            ) : (
              <div className="f6-matched-term-list">
                {alert.matched_terms.map((item, index) => (
                  <article key={`${item.filter}-${item.term}-${index}`}>
                    <span>{item.filter}</span>
                    <strong>{item.term}</strong>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="f6-detail-sidebar">
          <section className="f6-panel f6-review-card">
            <div className="f6-review-title">
              <div className="f6-review-icon">
                <ShieldCheck size={19} />
              </div>
              <div>
                <h2>Human review</h2>
                <p>Record an applicability assessment and review decision.</p>
              </div>
            </div>

            {isPending ? (
              <form className="f6-form" onSubmit={handleReview}>
                <label className="f6-field">
                  <span>Alert decision *</span>
                  <select
                    value={reviewStatus}
                    onChange={(event) =>
                      setReviewStatus(
                        event.target.value as "reviewed" | "dismissed"
                      )
                    }
                  >
                    <option value="reviewed">Mark as reviewed</option>
                    <option value="dismissed">Dismiss alert</option>
                  </select>
                </label>

                <label className="f6-field">
                  <span>Applicability assessment</span>
                  <select
                    value={applicability}
                    onChange={(event) =>
                      setApplicability(
                        event.target.value as ApplicabilityDecision | ""
                      )
                    }
                  >
                    <option value="">Not assessed</option>
                    <option value="applicable">Applicable</option>
                    <option value="not_applicable">Not applicable</option>
                    <option value="uncertain">Uncertain</option>
                  </select>
                </label>

                <label className="f6-field">
                  <span>Effective date</span>
                  <input
                    type="date"
                    value={effectiveAt}
                    onChange={(event) => setEffectiveAt(event.target.value)}
                  />
                  <small>
                    Optional. If supplied, the backend updates the
                    publication's effective date.
                  </small>
                </label>

                <label className="f6-field">
                  <span>Review notes</span>
                  <textarea
                    rows={5}
                    maxLength={5000}
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    placeholder="Record review reasoning, scope considerations or follow-up actions..."
                  />
                </label>

                {reviewError && (
                  <div className="f6-alert f6-alert-error" role="alert">
                    <AlertCircle size={15} />
                    <span>{reviewError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  className="f6-primary-button f6-full-button"
                  disabled={saving}
                >
                  {saving ? (
                    <LoaderCircle size={15} className="f6-spin" />
                  ) : reviewStatus === "reviewed" ? (
                    <CheckCircle2 size={15} />
                  ) : (
                    <XCircle size={15} />
                  )}
                  {saving
                    ? "Saving review..."
                    : reviewStatus === "reviewed"
                      ? "Save review"
                      : "Dismiss alert"}
                </button>
              </form>
            ) : (
              <div className="f6-reviewed-state">
                <CheckCircle2 size={22} />
                <strong>Review recorded</strong>
                <StatusBadge status={statusAppearance(alert.status)}>
                  {readable(alert.status)}
                </StatusBadge>

                <div>
                  <span>Reviewed at</span>
                  <strong>{dateLabel(alert.reviewed_at)}</strong>
                </div>

                <div>
                  <span>Reviewer ID</span>
                  <code>{alert.reviewed_by ?? "—"}</code>
                </div>

                <div>
                  <span>Review notes</span>
                  <p>{alert.review_notes || "No review notes supplied."}</p>
                </div>

                <p className="f6-reviewed-help">
                  The existing API does not provide a reopen endpoint.
                  This alert cannot be returned to pending from this screen.
                </p>
              </div>
            )}
          </section>

          {alert.document_id && (
            <section className="f6-panel f6-linked-document">
              <div className="f6-review-title">
                <div className="f6-review-icon f6-document-icon">
                  <FileText size={18} />
                </div>
                <div>
                  <h2>Indexed document</h2>
                  <p>This publication has an organization-scoped document link.</p>
                </div>
              </div>

              <Link
                to={`/documents/${alert.document_id}`}
                className="f6-document-link"
              >
                Open indexed document
                <ExternalLink size={14} />
              </Link>
            </section>
          )}

          <section className="f6-panel f6-audit-card">
            <h2>Review audit details</h2>

            <div>
              <span>Alert ID</span>
              <code>{alert.id}</code>
            </div>

            <div>
              <span>Publication ID</span>
              <code>{publication.id}</code>
            </div>

            <div>
              <span>Version ID</span>
              <code>{version.id}</code>
            </div>

            <div>
              <span>Reviewed at</span>
              <strong>{dateLabel(alert.reviewed_at)}</strong>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
