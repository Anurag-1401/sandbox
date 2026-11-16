
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { oidcManager } from "../../lib/oidc";
import { auth } from "../../lib/auth";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const started = useRef(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function completeSignIn() {
      if (!oidcManager) {
        setError("OIDC is not configured.");
        return;
      }

      try {
        const user = await oidcManager.signinRedirectCallback();

        if (!user.access_token || user.expired) {
          throw new Error("The identity provider returned an invalid session.");
        }

        auth.setAccessToken(user.access_token);
        navigate("/select-workspace", { replace: true });
      } catch (cause) {
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to complete authentication."
        );
      }
    }

    void completeSignIn();
  }, [navigate]);

  return (
    <div className="auth-loading">
      {error ? (
        <div className="auth-callback-error">
          <h2>Sign-in could not be completed</h2>
          <p>{error}</p>
          <button
            className="primary-button"
            onClick={() => navigate("/login", { replace: true })}
          >
            Return to sign in
          </button>
        </div>
      ) : (
        <>
          <div className="loading-spinner" />
          <p>Completing secure sign-in...</p>
        </>
      )}
    </div>
  );
}
