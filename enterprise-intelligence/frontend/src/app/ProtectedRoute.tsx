
import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "./AuthProvider";
import { useWorkspace } from "./WorkspaceProvider";

function LoadingScreen() {
  return (
    <div className="auth-loading">
      <div className="loading-spinner" />
      <p>Restoring your secure session...</p>
    </div>
  );
}

export function ProtectedRoute({
  children,
  requireWorkspace = true
}: {
  children: ReactNode;
  requireWorkspace?: boolean;
}) {
  const auth = useAuth();
  const workspace = useWorkspace();
  const location = useLocation();

  if (auth.status === "loading") {
    return <LoadingScreen />;
  }

  if (auth.status === "unconfigured") {
    return <Navigate to="/login" replace />;
  }

  if (auth.status !== "authenticated") {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  if (!requireWorkspace) {
    return <>{children}</>;
  }

  if (workspace.status === "loading") {
    return <LoadingScreen />;
  }

  if (!workspace.activeWorkspace) {
    return <Navigate to="/select-workspace" replace />;
  }

  return <>{children}</>;
}
