
import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowUpRight,
  LoaderCircle,
  RefreshCw,
  ShieldAlert,
  ShieldCheck
} from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { getApiErrorMessage } from "../../lib/api";

import {
  listInvestigations,
  type Investigation
} from "../investigations/investigations-api";

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

export function VerificationPage() {
  const [items, setItems] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadQueue = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);

    setError("");

    try {
      const data = await listInvestigations(100, 0);
      setItems(
        data.filter((item) => item.status === "review_required")
      );
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  return (
    <div className="f5-page">
      <PageHeader
        eyebrow="QUALITY AND EVIDENCE CONTROL"
        title="Verification Queue"
        description="Review completed investigations, inspect supporting evidence and record human decisions."
        actions={
          <button
            type="button"
            className="f5-secondary-button"
            onClick={() => void loadQueue(true)}
            disabled={refreshing}
          >
            {refreshing ? (
              <LoaderCircle size={16} className="f5-spin" />
            ) : (
              <RefreshCw size={16} />
            )}
            Refresh queue
          </button>
        }
      />

      <div className="f5-review-banner">
        <div className="f5-review-banner-icon">
          <ShieldAlert size={22} />
        </div>
        <div>
          <strong>Human approval is required</strong>
          <p>
            Automated claim verification and model confidence are decision
            support signals. Review the original evidence and limitations
            before approving an investigation.
          </p>
        </div>
      </div>

      <div className="f5-metric-row f5-review-metrics">
        <article className="f5-stat-card">
          <span>Awaiting review</span>
          <strong>{items.length}</strong>
          <small>Investigation records in this queue</small>
        </article>

        <article className="f5-stat-card">
          <span>Queue status</span>
          <strong className="f5-text-status">
            {loading ? "Loading" : error ? "Error" : "Live"}
          </strong>
          <small>Based on the latest API response</small>
        </article>
      </div>

      {error && (
        <div className="f5-alert f5-alert-error" role="alert">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
      )}

      <section className="f5-panel">
        <div className="f5-toolbar">
          <div>
            <h2>Pending human decisions</h2>
            <p>
              Each record links to the investigation report and its
              evidence-verification details.
            </p>
          </div>
          <StatusBadge status="warning">Review required</StatusBadge>
        </div>

        {loading ? (
          <div className="f5-loading">
            <LoaderCircle size={25} className="f5-spin" />
            <span>Loading review queue...</span>
          </div>
        ) : items.length === 0 ? (
          <div className="f5-empty">
            <div className="f5-empty-icon f5-success-icon">
              <ShieldCheck size={24} />
            </div>
            <h3>No investigations awaiting review</h3>
            <p>
              There are currently no investigation records in the
              review-required state for this organization.
            </p>
            <Link to="/investigations" className="f5-secondary-button">
              View investigations
              <ArrowUpRight size={15} />
            </Link>
          </div>
        ) : (
          <div className="f5-review-list">
            {items.map((item) => (
              <article className="f5-review-item" key={item.id}>
                <div className="f5-review-item-icon">
                  <ShieldAlert size={19} />
                </div>

                <div className="f5-review-item-content">
                  <div className="f5-review-item-heading">
                    <h3>{item.title}</h3>
                    <StatusBadge status="warning">
                      Review required
                    </StatusBadge>
                  </div>

                  <p>{item.question}</p>

                  <div className="f5-review-item-meta">
                    <span>Created {formatDate(item.created_at)}</span>
                    <span>Updated {formatDate(item.updated_at)}</span>
                  </div>
                </div>

                <Link
                  to={`/investigations/${item.id}?review=1`}
                  className="f5-review-open"
                  aria-label={`Review ${item.title}`}
                >
                  Review
                  <ArrowUpRight size={16} />
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
