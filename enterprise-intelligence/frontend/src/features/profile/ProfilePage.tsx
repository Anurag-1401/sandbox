import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { UserRound } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { enterpriseApi, type Profile } from "../../lib/enterprise-api";
import { getApiErrorMessage } from "../../lib/api";

export function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadProfile() {
    setLoading(true);
    setError(null);

    try {
      const result = await enterpriseApi.getProfile();
      setProfile(result);
      setDisplayName(result.display_name || "");
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProfile();
  }, []);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      await enterpriseApi.updateProfile(displayName);
      setMessage("Profile updated successfully.");
      await loadProfile();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="ACCOUNT"
        title="My profile"
        description="Manage your personal information and view your organization role."
      />

      {loading && <div className="page-loading">Loading profile...</div>}

      {error && <div className="form-alert error">{error}</div>}

      {profile && (
        <div className="settings-card">
          <div className="settings-card-heading">
            <div className="settings-card-icon">
              <UserRound size={20} />
            </div>
            <div>
              <h2>Personal information</h2>
              <p>Profile details associated with your account.</p>
            </div>
          </div>

          <form onSubmit={saveProfile} className="settings-form">
            <div className="form-field">
              <label>Email address</label>
              <input value={profile.email || ""} disabled />
              <span className="field-help">
                Email is managed by your identity provider.
              </span>
            </div>

            <div className="form-field">
              <label htmlFor="displayName">Display name</label>
              <input
                id="displayName"
                value={displayName}
                maxLength={200}
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Your display name"
              />
            </div>

            <div className="profile-readonly-grid">
              <div>
                <span>Organization role</span>
                <strong>{profile.role}</strong>
              </div>
              <div>
                <span>Account status</span>
                <strong>{profile.is_active ? "Active" : "Inactive"}</strong>
              </div>
            </div>

            {message && <div className="form-alert success">{message}</div>}

            <button
              className="primary-button"
              type="submit"
              disabled={saving}
            >
              {saving ? "Saving..." : "Save profile"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
