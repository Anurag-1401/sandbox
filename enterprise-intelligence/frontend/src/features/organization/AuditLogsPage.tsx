
import { useEffect, useState } from "react";
import { History } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import {
  enterpriseApi,
  type AuditLog
} from "../../lib/enterprise-api";

import { getApiErrorMessage } from "../../lib/api";

export function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const result = await enterpriseApi.getAuditLogs();

        if (active) setLogs(result);
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

  return (
    <div>
      <PageHeader
        eyebrow="GOVERNANCE"
        title="Audit activity"
        description="Review recorded organization-level management events."
      />

      {error && <div className="form-alert error">{error}</div>}

      <div className="table-card">
        <div className="table-card-heading">
          <div>
            <h2>Organization audit log</h2>
            <p>Most recent records returned by the audit API.</p>
          </div>
          <div className="table-heading-icon"><History size={19} /></div>
        </div>

        {loading ? (
          <div className="page-loading">Loading audit logs...</div>
        ) : logs.length === 0 ? (
          <div className="empty-state compact">
            <h3>No audit records returned</h3>
            <p>No visible audit records were returned by the API.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Actor</th>
                  <th>Resource ID</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <StatusBadge status="info">{log.action}</StatusBadge>
                    </td>
                    <td>{log.resource_type}</td>
                    <td>{log.actor_id || "System / unknown"}</td>
                    <td>{log.resource_id || "—"}</td>
                    <td>{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
