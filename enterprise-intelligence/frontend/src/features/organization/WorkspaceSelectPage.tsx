import { useState } from "react";
import { Building2, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../app/AuthProvider";
import { useWorkspace } from "../../app/WorkspaceProvider";
import { getApiErrorMessage } from "../../lib/api";

export function WorkspaceSelectPage() {
  const navigate = useNavigate();

  const { logout } = useAuth();

  const {
    status,
    workspaces,
    error: workspaceError,
    selectWorkspace
  } = useWorkspace();

  const [organizationId, setOrganizationId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function chooseWorkspace(id: string) {
    setSubmitting(true);
    setError(null);

    try {
      await selectWorkspace(id);
      navigate("/dashboard", { replace: true });
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="workspace-select-page">
      <div className="workspace-select-card">
        <div className="workspace-select-icon">
          <Building2 size={26} />
        </div>

        <div className="auth-eyebrow">ORGANIZATION CONTEXT</div>
        <h1>Select your workspace</h1>
        <p className="workspace-select-description">
          Choose the organization whose documents, investigations
          and intelligence data you want to access.
        </p>

        {status === "loading" && (
          <div className="inline-loading">
            <div className="loading-spinner small" />
            Checking organization membership...
          </div>
        )}

        {workspaces.length > 0 && (
          <div className="workspace-options">
            {workspaces.map((workspace) => (
              <button
                className="workspace-option"
                key={workspace.organization_id}
                type="button"
                disabled={submitting}
                onClick={() =>
                  void chooseWorkspace(workspace.organization_id)
                }
              >
                <div className="workspace-option-mark">
                  <Building2 size={18} />
                </div>
                <div className="workspace-option-copy">
                  <strong>{workspace.name}</strong>
                  <span>
                    {workspace.industry || "Organization"} · {workspace.role}
                  </span>
                </div>
                <span className="workspace-option-arrow">→</span>
              </button>
            ))}
          </div>
        )}

        <div className="workspace-manual-entry">
          <label htmlFor="organizationId">
            Organization ID
          </label>
          <input
            id="organizationId"
            value={organizationId}
            onChange={(event) => setOrganizationId(event.target.value)}
            placeholder="Enter your organization UUID"
          />
          <button
            className="secondary-button"
            type="button"
            disabled={!organizationId.trim() || submitting}
            onClick={() => void chooseWorkspace(organizationId)}
          >
            {submitting ? "Verifying..." : "Verify organization"}
          </button>
        </div>

        {(error || workspaceError) && (
          <div className="form-alert error">
            {error || workspaceError}
          </div>
        )}

        <button
          className="text-button logout-link"
          type="button"
          onClick={() => void logout()}
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </div>
  );
}
