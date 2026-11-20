
import { api } from "./api";

export interface WorkspaceSummary {
  organization_id: string;
  name: string;
  industry?: string | null;
  role: OrganizationRole;
}

export interface Workspace {
  id: string;
  name: string;
  industry: string | null;
  timezone: string;
  settings: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export type OrganizationRole =
  | "owner"
  | "admin"
  | "analyst"
  | "reviewer";

export interface Profile {
  id: string;
  email: string | null;
  display_name: string | null;
  is_active: boolean;
  organization_id: string;
  role: OrganizationRole;
}

export interface Member {
  user_id: string;
  email: string | null;
  display_name: string | null;
  role: OrganizationRole;
  status: "active" | "invited" | "suspended";
  department_id: string | null;
  joined_at: string;
}

export interface Department {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface DashboardMetrics {
  organization_id: string;
  total_members: number;
  active_members: number;
  total_documents: number;
  total_investigations: number;
  investigations_by_status: Record<string, number>;
  total_departments: number;
  pending_invitations: number;
}

export interface AuditLog {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface InvitationResult {
  invitation: {
    id: string;
    email: string;
    role: OrganizationRole;
    department_id: string | null;
    expires_at: string;
    created_at: string;
  };
  token: string;
}

export const enterpriseApi = {
  async getWorkspaces(organizationId?: string) {
    const response = await api.get<WorkspaceSummary[]>(
      "/enterprise/workspaces",
      organizationId
        ? { headers: { "X-Organization-ID": organizationId } }
        : undefined
    );

    return response.data;
  },

  async getWorkspace(organizationId?: string) {
    const response = await api.get<Workspace>(
      "/enterprise/workspace",
      organizationId
        ? { headers: { "X-Organization-ID": organizationId } }
        : undefined
    );

    return response.data;
  },

  async createWorkspace(payload: {
  name: string;
  industry: string | null;
  timezone: string;
}) {
  const response = await api.post<WorkspaceSummary>(
    "/enterprise/workspaces",
    payload
  );

  return response.data;
},

  async updateWorkspace(
    payload: Partial<Pick<Workspace, "name" | "industry" | "timezone" | "settings">>
  ) {
    const response = await api.patch<Workspace>(
      "/enterprise/workspace",
      payload
    );

    return response.data;
  },

  
async getProfile(organizationId?: string) {
  const response = await api.get<Profile>(
    "/enterprise/profile",
    organizationId
      ? { headers: { "X-Organization-ID": organizationId } }
      : undefined
  );

  return response.data;
},


  async updateProfile(display_name: string) {
    const response = await api.patch<Partial<Profile>>(
      "/enterprise/profile",
      { display_name }
    );

    return response.data;
  },

  async getMembers(limit = 100, offset = 0) {
    const response = await api.get<Member[]>("/enterprise/members", {
      params: { limit, offset }
    });

    return response.data;
  },

  async updateMemberRole(userId: string, role: OrganizationRole) {
    const response = await api.patch(
      `/enterprise/members/${userId}/role`,
      { role }
    );

    return response.data;
  },

  async updateMemberStatus(userId: string, active: boolean) {
    const response = await api.patch(
      `/enterprise/members/${userId}/status`,
      null,
      { params: { active } }
    );

    return response.data;
  },

  async assignMemberDepartment(
    userId: string,
    department_id: string | null
  ) {
    const response = await api.patch(
      `/enterprise/members/${userId}/department`,
      { department_id }
    );

    return response.data;
  },

  async createInvitation(payload: {
    email: string;
    role: "admin" | "analyst" | "reviewer";
    department_id: string | null;
  }) {
    const response = await api.post<InvitationResult>(
      "/enterprise/invitations",
      payload
    );

    return response.data;
  },

  async getDepartments() {
    const response = await api.get<Department[]>(
      "/enterprise/departments"
    );

    return response.data;
  },

  async createDepartment(payload: {
    name: string;
    description: string | null;
  }) {
    const response = await api.post<Department>(
      "/enterprise/departments",
      payload
    );

    return response.data;
  },

  async getDashboard() {
    const response = await api.get<DashboardMetrics>(
      "/enterprise/dashboard"
    );

    return response.data;
  },

  async getAuditLogs(limit = 100, offset = 0) {
    const response = await api.get<AuditLog[]>(
      "/enterprise/audit-logs",
      { params: { limit, offset } }
    );

    return response.data;
  }
};
