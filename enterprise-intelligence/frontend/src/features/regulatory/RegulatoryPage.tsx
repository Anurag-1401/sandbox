
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  Bell,
  CheckCircle2,
  ChevronRight,
  FileText,
  Filter,
  Globe2,
  LoaderCircle,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  X
} from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { getApiErrorMessage } from "../../lib/api";

import {
  createRegulatorySubscription,
  deactivateRegulatorySubscription,
  getRegulatoryAlerts,
  getRegulatorySources,
  getRegulatorySubscriptions,
  type RegulatoryAlert,
  type RegulatorySource,
  type RegulatorySubscription,
  type SubscriptionCreateRequest
} from "./regulatory-api";

type Tab = "alerts" | "sources" | "subscriptions";

const FILTER_FIELDS = [
  { key: "industries", label: "Industries" },
  { key: "products", label: "Products" },
  { key: "jurisdictions", label: "Jurisdictions" },
  { key: "keywords", label: "Keywords" }
] as const;

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

function splitTerms(value: string): string[] {
  return value
    .split(/[\n,;]+/)
    .map((term) => term.trim())
    .filter(Boolean);
}

export function RegulatoryPage() {
  const [activeTab, setActiveTab] = useState<Tab>("alerts");

  const [sources, setSources] = useState<RegulatorySource[]>([]);
  const [subscriptions, setSubscriptions] = useState<
    RegulatorySubscription[]
  >([]);
  const [alerts, setAlerts] = useState<RegulatoryAlert[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [filterValues, setFilterValues] = useState({
    industries: "",
    products: "",
    jurisdictions: "",
    keywords: ""
  });

  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");
  const [deactivatingId, setDeactivatingId] = useState<string | null>(null);

  const loadWorkspace = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);

    setError("");

    try {
      const [sourceData, subscriptionData, alertData] =
        await Promise.all([
          getRegulatorySources(),
          getRegulatorySubscriptions(),
          getRegulatoryAlerts(undefined, 100, 0)
        ]);

      setSources(sourceData);
      setSubscriptions(subscriptionData);
      setAlerts(alertData);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  const activeSubscriptions = subscriptions.filter(
    (item) => item.active
  );

  const pendingAlerts = alerts.filter(
    (item) => item.status === "pending"
  );

  const filteredAlerts = useMemo(() => {
    const term = search.trim().toLowerCase();

    return alerts.filter((alert) => {
      const matchesSearch =
        !term ||
        alert.title.toLowerCase().includes(term) ||
        alert.summary.toLowerCase().includes(term);

      const matchesStatus =
        statusFilter === "all" ||
        alert.status === statusFilter;

      const matchesSeverity =
        severityFilter === "all" ||
        alert.severity === severityFilter;

      return matchesSearch && matchesStatus && matchesSeverity;
    });
  }, [alerts, search, statusFilter, severityFilter]);

  const subscribedSourceIds = new Set(
    activeSubscriptions.map((item) => item.source_id)
  );

  function openSubscriptionModal(sourceId = "") {
    setSelectedSourceId(sourceId);
    setFilterValues({
      industries: "",
      products: "",
      jurisdictions: "",
      keywords: ""
    });
    setActionError("");
    setActionSuccess("");
    setModalOpen(true);
  }

  async function handleSubscribe(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError("");
    setActionSuccess("");

    if (!selectedSourceId) {
      setActionError("Select a regulatory source.");
      return;
    }

    const filters: SubscriptionCreateRequest["filters"] = {};

    for (const field of FILTER_FIELDS) {
      const terms = splitTerms(filterValues[field.key]);

      if (terms.length > 0) {
        filters[field.key] = terms;
      }
    }

    setSaving(true);

    try {
      await createRegulatorySubscription({
        source_id: selectedSourceId,
        filters
      });

      setModalOpen(false);
      setActionSuccess(
        "Regulatory source subscription saved successfully."
      );

      await loadWorkspace(true);
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(subscriptionId: string) {
    const confirmed = window.confirm(
      "Deactivate this regulatory source subscription?"
    );

    if (!confirmed) return;

    setDeactivatingId(subscriptionId);
    setActionError("");
    setActionSuccess("");

    try {
      await deactivateRegulatorySubscription(subscriptionId);

      setActionSuccess("Subscription deactivated.");
      await loadWorkspace(true);
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    } finally {
      setDeactivatingId(null);
    }
  }

  const sourceById = new Map(
    sources.map((source) => [source.id, source])
  );

  return (
    <div className="f6-page">
      <PageHeader
        eyebrow="REGULATORY INTELLIGENCE"
        title="Regulatory Monitoring"
        description="Monitor subscribed regulatory sources, review detected publications and track potential changes affecting your organization."
        actions={
          <button
            type="button"
            className="f6-primary-button"
            onClick={() => openSubscriptionModal()}
          >
            <Plus size={16} />
            Subscribe to source
          </button>
        }
      />

      {error && (
        <div className="f6-alert f6-alert-error" role="alert">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
      )}

      {actionError && (
        <div className="f6-alert f6-alert-error" role="alert">
          <AlertCircle size={17} />
          <span>{actionError}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="f6-alert f6-alert-success" role="status">
          <CheckCircle2 size={17} />
          <span>{actionSuccess}</span>
        </div>
      )}

      <section className="f6-stat-grid">
        <article className="f6-stat-card">
          <div className="f6-stat-icon">
            <Globe2 size={18} />
          </div>
          <span>Available sources</span>
          <strong>{sources.length}</strong>
          <small>Enabled platform sources</small>
        </article>

        <article className="f6-stat-card">
          <div className="f6-stat-icon">
            <Activity size={18} />
          </div>
          <span>Active subscriptions</span>
          <strong>{activeSubscriptions.length}</strong>
          <small>Sources monitored for this organization</small>
        </article>

        <article className="f6-stat-card">
          <div className="f6-stat-icon f6-warning-icon">
            <Bell size={18} />
          </div>
          <span>Pending alerts</span>
          <strong>{pendingAlerts.length}</strong>
          <small>Awaiting human review</small>
        </article>

        <article className="f6-stat-card">
          <div className="f6-stat-icon f6-success-icon">
            <ShieldCheck size={18} />
          </div>
          <span>Reviewed alerts</span>
          <strong>
            {alerts.filter((item) => item.status === "reviewed").length}
          </strong>
          <small>Reviewed in the loaded alert set</small>
        </article>
      </section>

      <section className="f6-panel">
        <div className="f6-tabs" role="tablist" aria-label="Regulatory sections">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "alerts"}
            className={activeTab === "alerts" ? "active" : ""}
            onClick={() => setActiveTab("alerts")}
          >
            <Bell size={15} />
            Alerts
            <span>{pendingAlerts.length}</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "sources"}
            className={activeTab === "sources" ? "active" : ""}
            onClick={() => setActiveTab("sources")}
          >
            <Globe2 size={15} />
            Sources
            <span>{sources.length}</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "subscriptions"}
            className={activeTab === "subscriptions" ? "active" : ""}
            onClick={() => setActiveTab("subscriptions")}
          >
            <Activity size={15} />
            Subscriptions
            <span>{subscriptions.length}</span>
          </button>
        </div>

        <div className="f6-panel-body">
          <div className="f6-section-toolbar">
            <div>
              <h2>
                {activeTab === "alerts"
                  ? "Regulatory alerts"
                  : activeTab === "sources"
                    ? "Official regulatory sources"
                    : "Organization subscriptions"}
              </h2>
              <p>
                {activeTab === "alerts"
                  ? "Publications and publication changes detected by the monitoring service."
                  : activeTab === "sources"
                    ? "Platform-managed sources that are enabled for monitoring."
                    : "Configure which sources your organization follows and the relevance terms used for screening."}
              </p>
            </div>

            <button
              type="button"
              className="f6-icon-button"
              onClick={() => void loadWorkspace(true)}
              disabled={refreshing}
              aria-label="Refresh regulatory data"
              title="Refresh"
            >
              {refreshing ? (
                <LoaderCircle size={16} className="f6-spin" />
              ) : (
                <RefreshCw size={16} />
              )}
            </button>
          </div>

          {activeTab === "alerts" && (
            <>
              <div className="f6-filter-row">
                <label className="f6-search">
                  <Search size={15} />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search alerts..."
                  />
                </label>

                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                  aria-label="Filter alert status"
                >
                  <option value="all">All statuses</option>
                  <option value="pending">Pending</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="dismissed">Dismissed</option>
                </select>

                <select
                  value={severityFilter}
                  onChange={(event) => setSeverityFilter(event.target.value)}
                  aria-label="Filter alert severity"
                >
                  <option value="all">All severity</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="info">Info</option>
                </select>
              </div>

              {loading ? (
                <div className="f6-loading">
                  <LoaderCircle size={24} className="f6-spin" />
                  Loading regulatory alerts...
                </div>
              ) : filteredAlerts.length === 0 ? (
                <div className="f6-empty">
                  <div className="f6-empty-icon">
                    <Bell size={23} />
                  </div>
                  <h3>No matching regulatory alerts</h3>
                  <p>
                    Alerts appear here after the monitoring worker discovers
                    new publications or changed publication versions for
                    subscribed sources.
                  </p>
                </div>
              ) : (
                <div className="f6-alert-list">
                  {filteredAlerts.map((alert) => (
                    <article className="f6-alert-card" key={alert.id}>
                      <div className="f6-alert-card-icon">
                        <FileText size={18} />
                      </div>

                      <div className="f6-alert-card-content">
                        <div className="f6-alert-card-heading">
                          <Link
                            to={`/regulatory/alerts/${alert.id}`}
                            className="f6-alert-title"
                          >
                            {alert.title}
                          </Link>

                          <div className="f6-badge-row">
                            <StatusBadge
                              status={severityAppearance(alert.severity)}
                            >
                              {alert.severity}
                            </StatusBadge>

                            <StatusBadge
                              status={statusAppearance(alert.status)}
                            >
                              {readable(alert.status)}
                            </StatusBadge>
                          </div>
                        </div>

                        <p>{alert.summary}</p>

                        <div className="f6-alert-meta">
                          <span>{readable(alert.alert_type)}</span>
                          <span>{readable(alert.relevance_status)}</span>
                          <span>{dateLabel(alert.created_at)}</span>
                        </div>

                        {alert.matched_terms.length > 0 && (
                          <div className="f6-matched-terms">
                            {alert.matched_terms.map((item, index) => (
                              <span key={`${item.filter}-${item.term}-${index}`}>
                                {item.filter}: {item.term}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      <Link
                        to={`/regulatory/alerts/${alert.id}`}
                        className="f6-open-alert"
                        aria-label={`Open alert ${alert.title}`}
                      >
                        <ChevronRight size={18} />
                      </Link>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === "sources" && (
            loading ? (
              <div className="f6-loading">
                <LoaderCircle size={24} className="f6-spin" />
                Loading sources...
              </div>
            ) : sources.length === 0 ? (
              <div className="f6-empty">
                <div className="f6-empty-icon">
                  <Globe2 size={23} />
                </div>
                <h3>No enabled sources available</h3>
                <p>
                  No enabled regulatory sources were returned by the backend.
                </p>
              </div>
            ) : (
              <div className="f6-source-grid">
                {sources.map((source) => {
                  const subscribed = subscribedSourceIds.has(source.id);

                  return (
                    <article className="f6-source-card" key={source.id}>
                      <div className="f6-source-card-top">
                        <div className="f6-source-icon">
                          <Globe2 size={18} />
                        </div>

                        <StatusBadge status={subscribed ? "success" : "neutral"}>
                          {subscribed ? "Subscribed" : "Not subscribed"}
                        </StatusBadge>
                      </div>

                      <span className="f6-source-code">{source.code}</span>
                      <h3>{source.name}</h3>
                      <p>{source.authority}</p>

                      <div className="f6-source-meta">
                        <span>Jurisdiction</span>
                        <strong>{source.jurisdiction}</strong>
                        <span>Source type</span>
                        <strong>{source.source_type.toUpperCase()}</strong>
                        <span>Scan interval</span>
                        <strong>{source.scan_interval_minutes} minutes</strong>
                      </div>

                      <button
                        type="button"
                        className={
                          subscribed
                            ? "f6-secondary-button"
                            : "f6-primary-button"
                        }
                        disabled={subscribed}
                        onClick={() => openSubscriptionModal(source.id)}
                      >
                        {subscribed ? (
                          <>
                            <CheckCircle2 size={15} />
                            Subscribed
                          </>
                        ) : (
                          <>
                            <Plus size={15} />
                            Subscribe
                          </>
                        )}
                      </button>
                    </article>
                  );
                })}
              </div>
            )
          )}

          {activeTab === "subscriptions" && (
            loading ? (
              <div className="f6-loading">
                <LoaderCircle size={24} className="f6-spin" />
                Loading subscriptions...
              </div>
            ) : subscriptions.length === 0 ? (
              <div className="f6-empty">
                <div className="f6-empty-icon">
                  <Activity size={23} />
                </div>
                <h3>No subscriptions configured</h3>
                <p>
                  Subscribe to a source to begin receiving organization-scoped
                  regulatory alerts.
                </p>
                <button
                  type="button"
                  className="f6-primary-button"
                  onClick={() => openSubscriptionModal()}
                >
                  <Plus size={15} />
                  Add subscription
                </button>
              </div>
            ) : (
              <div className="f6-subscription-list">
                {subscriptions.map((subscription) => {
                  const source = sourceById.get(subscription.source_id);

                  return (
                    <article
                      className="f6-subscription-card"
                      key={subscription.id}
                    >
                      <div className="f6-subscription-icon">
                        <Activity size={18} />
                      </div>

                      <div className="f6-subscription-content">
                        <div className="f6-subscription-heading">
                          <strong>
                            {source?.name ?? subscription.source_id}
                          </strong>
                          <StatusBadge
                            status={subscription.active ? "success" : "neutral"}
                          >
                            {subscription.active ? "Active" : "Inactive"}
                          </StatusBadge>
                        </div>

                        <small>
                          Created {dateLabel(subscription.created_at)}
                        </small>

                        <div className="f6-filter-chips">
                          {FILTER_FIELDS.flatMap((field) =>
                            (subscription.filters[field.key] ?? []).map(
                              (term) => (
                                <span key={`${field.key}-${term}`}>
                                  {field.label}: {term}
                                </span>
                              )
                            )
                          )}

                          {Object.values(subscription.filters).every(
                            (values) => !values || values.length === 0
                          ) && (
                            <span>No relevance filters configured</span>
                          )}
                        </div>
                      </div>

                      {subscription.active && (
                        <button
                          type="button"
                          className="f6-deactivate-button"
                          onClick={() =>
                            void handleDeactivate(subscription.id)
                          }
                          disabled={deactivatingId === subscription.id}
                        >
                          {deactivatingId === subscription.id ? (
                            <LoaderCircle size={15} className="f6-spin" />
                          ) : (
                            <X size={15} />
                          )}
                          Deactivate
                        </button>
                      )}
                    </article>
                  );
                })}
              </div>
            )
          )}
        </div>
      </section>

      <div className="f6-monitoring-note">
        <Filter size={16} />
        <p>
          Relevance filters provide candidate screening signals. A keyword
          match does not establish that a regulation legally applies to your
          organization. Human review is required.
        </p>
      </div>

      {modalOpen && (
        <div
          className="f6-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget &&
              !saving
            ) {
              setModalOpen(false);
            }
          }}
        >
          <section
            className="f6-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="f6-subscription-title"
          >
            <div className="f6-modal-header">
              <div>
                <span className="f6-eyebrow">SOURCE CONFIGURATION</span>
                <h2 id="f6-subscription-title">Subscribe to regulatory source</h2>
                <p>
                  Configure terms used to screen publications for potential
                  organizational relevance.
                </p>
              </div>

              <button
                type="button"
                className="f6-icon-button"
                onClick={() => setModalOpen(false)}
                disabled={saving}
                aria-label="Close subscription dialog"
              >
                <X size={18} />
              </button>
            </div>

            <form className="f6-form" onSubmit={handleSubscribe}>
              <label className="f6-field">
                <span>Regulatory source *</span>
                <select
                  value={selectedSourceId}
                  onChange={(event) => setSelectedSourceId(event.target.value)}
                  required
                >
                  <option value="">Select a source</option>
                  {sources.map((source) => (
                    <option value={source.id} key={source.id}>
                      {source.name} — {source.jurisdiction}
                    </option>
                  ))}
                </select>
              </label>

              <div className="f6-form-note">
                Leave a filter blank if you do not want to constrain screening
                by that category. If every filter is blank, the backend marks
                publications for manual triage.
              </div>

              {FILTER_FIELDS.map((field) => (
                <label className="f6-field" key={field.key}>
                  <span>{field.label}</span>
                  <textarea
                    rows={2}
                    value={filterValues[field.key]}
                    onChange={(event) =>
                      setFilterValues((current) => ({
                        ...current,
                        [field.key]: event.target.value
                      }))
                    }
                    placeholder={`Enter ${field.label.toLowerCase()}, separated by commas or new lines`}
                  />
                </label>
              ))}

              {actionError && (
                <div className="f6-alert f6-alert-error" role="alert">
                  <AlertCircle size={16} />
                  <span>{actionError}</span>
                </div>
              )}

              <div className="f6-modal-actions">
                <button
                  type="button"
                  className="f6-secondary-button"
                  onClick={() => setModalOpen(false)}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="f6-primary-button"
                  disabled={saving}
                >
                  {saving ? (
                    <LoaderCircle size={15} className="f6-spin" />
                  ) : (
                    <Plus size={15} />
                  )}
                  Save subscription
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
