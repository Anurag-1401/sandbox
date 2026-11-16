
import type { OrganizationRole } from "./enterprise-api";

export type Permission =
  | "workspace:read"
  | "workspace:update"
  | "members:read"
  | "members:invite"
  | "members:update"
  | "members:remove"
  | "departments:read"
  | "departments:manage"
  | "audit:read"
  | "documents:read"
  | "documents:manage"
  | "investigations:create"
  | "investigations:review";

const allPermissions: Permission[] = [
  "workspace:read",
  "workspace:update",
  "members:read",
  "members:invite",
  "members:update",
  "members:remove",
  "departments:read",
  "departments:manage",
  "audit:read",
  "documents:read",
  "documents:manage",
  "investigations:create",
  "investigations:review"
];

const rolePermissions: Record<OrganizationRole, Permission[]> = {
  owner: allPermissions,

  admin: [
    "workspace:read",
    "workspace:update",
    "members:read",
    "members:invite",
    "members:update",
    "members:remove",
    "departments:read",
    "departments:manage",
    "audit:read",
    "documents:read",
    "documents:manage",
    "investigations:create",
    "investigations:review"
  ],

  analyst: [
    "workspace:read",
    "members:read",
    "departments:read",
    "documents:read",
    "documents:manage",
    "investigations:create"
  ],

  reviewer: [
    "workspace:read",
    "members:read",
    "departments:read",
    "documents:read",
    "investigations:review"
  ]
};

export function hasPermission(
  role: OrganizationRole | undefined,
  permission: Permission
): boolean {
  if (!role) return false;

  return rolePermissions[role]?.includes(permission) ?? false;
}

export function hasAnyPermission(
  role: OrganizationRole | undefined,
  permissions: Permission[]
): boolean {
  return permissions.some((permission) =>
    hasPermission(role, permission)
  );
}
