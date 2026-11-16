
import { useEffect, useState } from "react";

import {
  ArrowUpRight,
  FileText,
  Layers3,
  Workflow,
  ShieldCheck
} from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";

import {
  documentsApi,
  type DocumentProcessingSummary
} from "../documents/documents-api";

import { getApiErrorMessage } from "../../lib/api";

export function DashboardPage() {
  const [summary, setSummary] =
    useState<DocumentProcessingSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await documentsApi.summary();

        if (active) setSummary(result);
      } catch (cause) {
        if (active) setError(getApiErrorMessage(cause));
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, []);

  const metrics = [
    {
      label: "Total documents",
      value: summary?.total_documents,
      note: "Documents in active organization",
      icon: FileText
    },
    {
      label: "Indexed documents",
      value: summary?.indexed_documents,
      note: "Successfully indexed",
      icon: ShieldCheck
    },
    {
      label: "Document versions",
      value: summary?.total_versions,
      note: "Stored document versions",
      icon: Layers3
    },
    {
      label: "Indexed chunks",
      value: summary?.total_chunks,
      note: "Searchable content chunks",
      icon: Workflow
    }
  ];

  return (
    <div className="dashboard-page">
      <PageHeader
        eyebrow="INTELLIGENCE OVERVIEW"
        title="Workspace overview"
        description="Monitor document ingestion and indexing across your organization."
      />

      <div className="welcome-panel">
        <div>
          <div className="welcome-kicker">
            ENTERPRISE INTELLIGENCE PLATFORM
          </div>

          <h2>Your intelligence workspace.</h2>

          <p>
            Upload source documents, extract content, create searchable
            evidence and build the foundation for investigations.
          </p>
        </div>

        <div className="welcome-visual" aria-hidden="true">
          <div className="visual-ring ring-one" />
          <div className="visual-ring ring-two" />
          <div className="visual-core">
            <Workflow size={32} />
          </div>
        </div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Document intelligence metrics</h2>
          <p>Values retrieved from the authenticated document API.</p>
        </div>

        <StatusBadge
          status={error ? "danger" : loading ? "neutral" : "success"}
        >
          {error ? "API error" : loading ? "Loading" : "Live API"}
        </StatusBadge>
      </div>

      {error && <div className="form-alert error">{error}</div>}

      <div className="metric-grid">
        {metrics.map(({ label, value, note, icon: Icon }) => (
          <article className="metric-card" key={label}>
            <div className="metric-card-top">
              <span className="metric-icon">
                <Icon size={19} />
              </span>
              <ArrowUpRight size={16} className="metric-arrow" />
            </div>

            <div className="metric-value">
              {loading ? "—" : (value ?? 0).toLocaleString()}
            </div>

            <div className="metric-label">{label}</div>
            <div className="metric-note">{note}</div>
          </article>
        ))}
      </div>

      {summary && (
        <>
          <div className="section-heading lower-heading">
            <div>
              <h2>Ingestion status</h2>
              <p>Current document processing totals.</p>
            </div>
          </div>

          <div className="document-status-summary">
            <div>
              <span>Indexed</span>
              <strong>{summary.indexed_documents}</strong>
            </div>

            <div>
              <span>Processing</span>
              <strong>{summary.processing_documents}</strong>
            </div>

            <div>
              <span>Failed</span>
              <strong>{summary.failed_documents}</strong>
            </div>
          </div>
        </>
      )}

      <div className="section-heading lower-heading">
        <div>
          <h2>Investigation and verification metrics</h2>
          <p>
            These will be connected to their respective backend APIs
            in the following frontend milestones.
          </p>
        </div>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon">
          <Workflow size={22} />
        </div>
        <h3>Investigation analytics are not connected yet</h3>
        <p>
          Document ingestion and indexing are now the live metrics
          available in this dashboard.
        </p>
      </div>
    </div>
  );
}
