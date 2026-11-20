import { useState, type FormEvent } from "react";
import {
  Building2,
  LogOut,
  Plus,
  ArrowRight
} from "lucide-react";
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
    selectWorkspace,
    createWorkspace
  } = useWorkspace();

  const [showCreateForm, setShowCreateForm] = useState(
    workspaces.length === 0
  );

  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");

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

  async function handleCreateWorkspace(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (name.trim().length < 2) {
      setError("Organization name must contain at least 2 characters.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await createWorkspace({
        name: name.trim(),
        industry: industry.trim() || null,
        timezone
      });

      navigate("/dashboard", { replace: true });

    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="workspace-select-page">
      <section className="workspace-select-card">

        <div className="workspace-select-icon">
          <Building2 size={26} />
        </div>

        <div className="auth-eyebrow">
          ENTERPRISE INTELLIGENCE
        </div>

        <h1>Welcome to your workspace</h1>

        <p className="workspace-select-description">
          Select an organization to continue, or create a new
          organization to start your own secure intelligence workspace.
        </p>

        {status === "loading" && (
          <div className="inline-loading">
            <div className="loading-spinner small" />
            Loading your organizations...
          </div>
        )}

        {status !== "loading" && workspaces.length > 0 && (
          <div className="workspace-section">
            <h2>Your organizations</h2>

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
                      {workspace.industry || "Organization"} ·{" "}
                      {workspace.role}
                    </span>
                  </div>

                  <ArrowRight size={18} />
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="workspace-create-section">

          <button
            className="workspace-create-toggle"
            type="button"
            onClick={() => {
              setShowCreateForm((value) => !value);
              setError(null);
            }}
          >
            <Plus size={18} />
            Create a new organization
          </button>

          {showCreateForm && (
            <form
              className="workspace-create-form"
              onSubmit={handleCreateWorkspace}
            >
              <h2>Set up your organization</h2>

              <p>
                You will automatically become the owner of
                this organization.
              </p>

              <label htmlFor="organizationName">
                Organization name
              </label>

              <input
                id="organizationName"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Example: Acme Intelligence"
                minLength={2}
                maxLength={255}
                required
              />

              <label htmlFor="organizationIndustry">
                Industry
              </label>

              <input
                id="organizationIndustry"
                value={industry}
                onChange={(event) => setIndustry(event.target.value)}
                placeholder="Example: Financial Services"
                maxLength={120}
              />

              <label htmlFor="organizationTimezone">
                Time zone
              </label>

              <select
                id="organizationTimezone"
                value={timezone}
                onChange={(event) => setTimezone(event.target.value)}
              >
                <option value="Asia/Kolkata">
                  India Standard Time
                </option>
                <option value="UTC">
                  UTC
                </option>
                <option value="America/New_York">
                  Eastern Time
                </option>
                <option value="Europe/London">
                  London
                </option>
                <option value="Asia/Singapore">
                  Singapore
                </option>
              </select>

              <button
                className="primary-button"
                type="submit"
                disabled={submitting}
              >
                {submitting
                  ? "Creating organization..."
                  : "Create organization"}
              </button>
            </form>
          )}
        </div>

        {(error || workspaceError) && (
          <div className="form-alert error" role="alert">
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

      </section>
    </main>
  );
}