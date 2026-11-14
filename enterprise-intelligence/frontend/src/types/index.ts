
export type OrganizationRole =
  | "owner"
  | "admin"
  | "analyst"
  | "reviewer";

export interface AuthenticatedUser {
  id: string;
  email: string;
  displayName?: string;
}

export interface OrganizationContext {
  id: string;
  name: string;
  role: OrganizationRole;
}

export interface ApiError {
  detail: string;
}
