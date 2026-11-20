
import { useEffect, useState ,type FormEvent} from "react";
import { Building2 } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { PermissionGate } from "../../app/PermissionGate";
import { useWorkspace } from "../../app/WorkspaceProvider";

import { enterpriseApi } from "../../lib/enterprise-api";
import { getApiErrorMessage } from "../../lib/api";

export function WorkspaceSettingsPage() {
  const { activeWorkspace, refreshWorkspace } = useWorkspace();

  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!activeWorkspace) return;

    setName(activeWorkspace.name);
    setIndustry(activeWorkspace.industry || "");
    setTimezone(activeWorkspace.timezone);
  }, [activeWorkspace]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await enterpriseApi.updateWorkspace({
        name,
        industry: industry || null,
        timezone
      });

      await refreshWorkspace();
      setSuccess("Workspace settings updated.");
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="ORGANIZATION MANAGEMENT"
        title="Workspace settings"
        description="Manage the details of your active organization."
      />

      {error && <div className="form-alert error">{error}</div>}
      {success && <div className="form-alert success">{success}</div>}

      <div className="settings-card">
        <div className="settings-card-heading">
          <div className="settings-card-icon"><Building2 size={20} /></div>
          <div>
            <h2>Organization details</h2>
            <p>These settings are scoped to the active organization.</p>
          </div>
        </div>

        <PermissionGate
          permission="workspace:update"
          fallback={
            <div className="form-alert info">
              Your role allows workspace viewing but not editing.
            </div>
          }
        >
          <form className="settings-form" onSubmit={save}>
            <div className="form-field">
              <label htmlFor="workspaceName">Organization name</label>
              <input
                id="workspaceName"
                value={name}
                onChange={(event) => setName(event.target.value)}
                minLength={2}
                maxLength={255}
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="industry">Industry</label>
              <input
                id="industry"
                value={industry}
                onChange={(event) => setIndustry(event.target.value)}
                maxLength={120}
              />
            </div>

            <div className="form-field">
              <label htmlFor="timezone">Timezone</label>
              <input
                id="timezone"
                value={timezone}
                onChange={(event) => setTimezone(event.target.value)}
                maxLength={80}
                required
              />
            </div>

            <button className="primary-button" disabled={saving}>
              {saving ? "Saving..." : "Save workspace"}
            </button>
          </form>
        </PermissionGate>
      </div>
    </div>
  );
}
