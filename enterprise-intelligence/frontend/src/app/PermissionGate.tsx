
import type { ReactNode } from "react";

import { useWorkspace } from "./WorkspaceProvider";
import {
  hasPermission,
  type Permission
} from "../lib/permissions";

export function PermissionGate({
  permission,
  children,
  fallback = null
}: {
  permission: Permission;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { activeWorkspace } = useWorkspace();

  if (!hasPermission(activeWorkspace?.role, permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
