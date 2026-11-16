
import { useState } from "react";
import { ShieldCheck, BrainCircuit, LockKeyhole } from "lucide-react";

import { useAuth } from "../../app/AuthProvider";
import { isOidcConfigured } from "../../config/env";

export function LoginPage() {
  const { login } = useAuth();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin() {
    setLoading(true);
    setError(null);

    try {
      await login();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to start sign-in."
      );
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand">
          <div className="brand-mark"><BrainCircuit size={23} /></div>
          <div>
            <strong>Enterprise Intelligence</strong>
            <span>RESEARCH & INVESTIGATION PLATFORM</span>
          </div>
        </div>

        <div className="auth-brand-content">
          <div className="auth-brand-icon">
            <ShieldCheck size={34} />
          </div>

          <h1>Intelligence built on evidence.</h1>

          <p>
            A connected workspace for document intelligence,
            regulatory monitoring, investigations and evidence-based
            decision support.
          </p>

          <div className="auth-security-note">
            <LockKeyhole size={15} />
            Secure organization-scoped access
          </div>
        </div>

        <div className="auth-brand-footer">
          ENTERPRISE INTELLIGENCE PLATFORM
        </div>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form">
          <div className="auth-mobile-brand">
            <div className="brand-mark"><BrainCircuit size={22} /></div>
            <strong>Enterprise Intelligence</strong>
          </div>

          <div className="auth-eyebrow">WELCOME BACK</div>
          <h2>Sign in to your workspace</h2>
          <p className="auth-description">
            Continue to your organization's intelligence workspace.
          </p>

          {!isOidcConfigured && (
            <div className="form-alert error">
              OIDC is not configured. Add the authority and client ID
              to your frontend environment file before signing in.
            </div>
          )}

          {error && (
            <div className="form-alert error">{error}</div>
          )}

          <button
            className="primary-button auth-submit"
            type="button"
            onClick={handleLogin}
            disabled={!isOidcConfigured || loading}
          >
            {loading ? "Redirecting..." : "Continue with secure sign-in"}
          </button>

          <div className="auth-provider-note">
            Authentication is managed by your configured identity provider.
          </div>

          <div className="auth-divider" />

          <div className="auth-trust">
            <ShieldCheck size={16} />
            Your organization and role determine your access.
          </div>
        </div>

        <div className="auth-bottom-note">
          © Enterprise Intelligence Platform
        </div>
      </section>
    </div>
  );
}
