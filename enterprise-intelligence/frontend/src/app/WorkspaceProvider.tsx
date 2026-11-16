
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";

import { useAuth } from "./AuthProvider";

import {
  enterpriseApi,
  type OrganizationRole,
  type Workspace,
  type WorkspaceSummary
} from "../lib/enterprise-api";

import {
  clearActiveOrganizationId,
  getActiveOrganizationId,
  setActiveOrganizationId
} from "../lib/workspace-context";

type ActiveWorkspace = Workspace & {
  role: OrganizationRole;
};

type WorkspaceStatus =
  | "loading"
  | "ready"
  | "needs-selection"
  | "error";

interface WorkspaceContextValue {
  status: WorkspaceStatus;
  activeWorkspace: ActiveWorkspace | null;
  workspaces: WorkspaceSummary[];
  error: string | null;
  selectWorkspace: (id: string) => Promise<void>;
  refreshWorkspace: () => Promise<void>;
  clearWorkspace: () => void;
}

const WorkspaceContext =
  createContext<WorkspaceContextValue | null>(null);

async function resolveWorkspace(id: string): Promise<ActiveWorkspace> {
  const [workspace, profile] = await Promise.all([
    enterpriseApi.getWorkspace(id),
    enterpriseApi.getProfile(id)
  ]);

  if (profile.organization_id !== id) {
    throw new Error("The selected organization context is invalid.");
  }

  if (!workspace.is_active) {
    throw new Error("This workspace is inactive.");
  }

  return {
    ...workspace,
    role: profile.role
  };
}

export function WorkspaceProvider({
  children
}: {
  children: ReactNode;
}) {
  const { status: authStatus } = useAuth();

  const [status, setStatus] = useState<WorkspaceStatus>("loading");

  const [activeWorkspace, setActiveWorkspace] =
    useState<ActiveWorkspace | null>(null);

  const [workspaces, setWorkspaces] =
    useState<WorkspaceSummary[]>([]);

  const [error, setError] = useState<string | null>(null);

  const selectWorkspace = useCallback(async (id: string) => {
    const normalizedId = id.trim();

    if (!normalizedId) {
      throw new Error("Enter an organization ID.");
    }

    setStatus("loading");
    setError(null);

    try {
      const workspace = await resolveWorkspace(normalizedId);

      setActiveOrganizationId(normalizedId);
      setActiveWorkspace(workspace);
      setStatus("ready");
    } catch (cause) {
      setStatus("needs-selection");
      throw cause;
    }
  }, []);

  const clearWorkspace = useCallback(() => {
    clearActiveOrganizationId();
    setActiveWorkspace(null);
    setStatus("needs-selection");
  }, []);

  const refreshWorkspace = useCallback(async () => {
    const id = getActiveOrganizationId();

    if (!id) {
      setActiveWorkspace(null);
      setStatus("needs-selection");
      return;
    }

    const workspace = await resolveWorkspace(id);
    setActiveWorkspace(workspace);
    setStatus("ready");
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      if (authStatus !== "authenticated") {
        setActiveWorkspace(null);
        setWorkspaces([]);
        setStatus(
          authStatus === "loading" ? "loading" : "needs-selection"
        );
        return;
      }

      setStatus("loading");
      setError(null);

      const savedId = getActiveOrganizationId();

      if (savedId) {
        try {
          const workspace = await resolveWorkspace(savedId);

          if (cancelled) return;

          setActiveWorkspace(workspace);
          setStatus("ready");

          try {
            const list = await enterpriseApi.getWorkspaces(savedId);

            if (!cancelled) {
              setWorkspaces(list);
            }
          } catch {
            if (!cancelled) setWorkspaces([]);
          }

          return;
        } catch {
          clearActiveOrganizationId();
        }
      }

      try {
        const list = await enterpriseApi.getWorkspaces();

        if (cancelled) return;

        setWorkspaces(list);

        if (list.length === 1) {
          const workspace = await resolveWorkspace(
            list[0].organization_id
          );

          if (cancelled) return;

          setActiveOrganizationId(list[0].organization_id);
          setActiveWorkspace(workspace);
          setStatus("ready");
          return;
        }

        setStatus("needs-selection");
      } catch {
        if (!cancelled) {
          setStatus("needs-selection");
          setError(
            "The backend could not resolve your organization automatically. " +
            "If you belong to multiple organizations, enter the organization ID."
          );
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
  }, [authStatus]);

  const value = useMemo(
    () => ({
      status,
      activeWorkspace,
      workspaces,
      error,
      selectWorkspace,
      refreshWorkspace,
      clearWorkspace
    }),
    [
      status,
      activeWorkspace,
      workspaces,
      error,
      selectWorkspace,
      refreshWorkspace,
      clearWorkspace
    ]
  );

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);

  if (!context) {
    throw new Error(
      "useWorkspace must be used inside WorkspaceProvider."
    );
  }

  return context;
}
