import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { MailPlus, RefreshCw, Users } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { PermissionGate } from "../../app/PermissionGate";
import { useWorkspace } from "../../app/WorkspaceProvider";

import {
  enterpriseApi,
  type Department,
  type InvitationResult,
  type Member,
  type OrganizationRole
} from "../../lib/enterprise-api";

import { getApiErrorMessage } from "../../lib/api";

export function TeamPage() {
  const { activeWorkspace } = useWorkspace();

  const [members, setMembers] = useState<Member[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<
    "admin" | "analyst" | "reviewer"
  >("analyst");
  const [inviteDepartment, setInviteDepartment] = useState("");
  const [inviting, setInviting] = useState(false);
  const [invitation, setInvitation] = useState<InvitationResult | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);

    try {
      const [memberData, departmentData] = await Promise.all([
        enterpriseApi.getMembers(),
        enterpriseApi.getDepartments()
      ]);

      setMembers(memberData);
      setDepartments(departmentData);
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function inviteMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setInviting(true);
    setError(null);
    setInvitation(null);

    try {
      const result = await enterpriseApi.createInvitation({
        email: inviteEmail,
        role: inviteRole,
        department_id: inviteDepartment || null
      });

      setInvitation(result);
      setInviteEmail("");
      await loadData();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setInviting(false);
    }
  }

  async function changeRole(userId: string, role: OrganizationRole) {
    try {
      await enterpriseApi.updateMemberRole(userId, role);
      await loadData();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    }
  }

  async function changeStatus(userId: string, active: boolean) {
    try {
      await enterpriseApi.updateMemberStatus(userId, active);
      await loadData();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    }
  }

  async function changeDepartment(
    userId: string,
    departmentId: string
  ) {
    try {
      await enterpriseApi.assignMemberDepartment(
        userId,
        departmentId || null
      );
      await loadData();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    }
  }

  const isOwner = activeWorkspace?.role === "owner";

  return (
    <div>
      <PageHeader
        eyebrow="ORGANIZATION MANAGEMENT"
        title="Team members"
        description="Manage organization membership, roles and department assignments."
        actions={
          <button
            className="secondary-button"
            onClick={() => void loadData()}
            type="button"
          >
            <RefreshCw size={15} />
            Refresh
          </button>
        }
      />

      {error && <div className="form-alert error">{error}</div>}

      <PermissionGate permission="members:invite">
        <div className="settings-card invite-card">
          <div className="settings-card-heading">
            <div className="settings-card-icon">
              <MailPlus size={20} />
            </div>
            <div>
              <h2>Invite a team member</h2>
              <p>
                Create an organization invitation. The returned token is
                displayed once for manual sharing.
              </p>
            </div>
          </div>

          <form className="invite-form" onSubmit={inviteMember}>
            <div className="form-field">
              <label htmlFor="inviteEmail">Email address</label>
              <input
                id="inviteEmail"
                type="email"
                required
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                placeholder="colleague@company.com"
              />
            </div>

            <div className="form-field">
              <label htmlFor="inviteRole">Role</label>
              <select
                id="inviteRole"
                value={inviteRole}
                onChange={(event) =>
                  setInviteRole(event.target.value as typeof inviteRole)
                }
              >
                {isOwner && <option value="admin">Admin</option>}
                <option value="analyst">Analyst</option>
                <option value="reviewer">Reviewer</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="inviteDepartment">Department</label>
              <select
                id="inviteDepartment"
                value={inviteDepartment}
                onChange={(event) =>
                  setInviteDepartment(event.target.value)
                }
              >
                <option value="">No department</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="primary-button invite-submit"
              type="submit"
              disabled={inviting}
            >
              {inviting ? "Creating..." : "Create invitation"}
            </button>
          </form>

          {invitation && (
            <div className="invitation-result">
              <strong>Invitation created</strong>
              <p>
                {invitation.invitation.email} · {invitation.invitation.role}
              </p>
              <label>Invitation token — share securely</label>
              <textarea readOnly value={invitation.token} rows={3} />
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  void navigator.clipboard.writeText(invitation.token)
                }
              >
                Copy token
              </button>
              <span className="field-help">
                The backend returns the raw token only once. No email delivery
                endpoint is present in the current backend module.
              </span>
            </div>
          )}
        </div>
      </PermissionGate>

      <div className="table-card">
        <div className="table-card-heading">
          <div>
            <h2>Organization members</h2>
            <p>
              {members.length} members returned by the current API request.
            </p>
          </div>
          <div className="table-heading-icon"><Users size={19} /></div>
        </div>

        {loading ? (
          <div className="page-loading">Loading members...</div>
        ) : members.length === 0 ? (
          <div className="empty-state compact">
            <h3>No members returned</h3>
            <p>There are no visible organization memberships to display.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Department</th>
                  <th>Joined</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.user_id}>
                    <td>
                      <strong>{member.display_name || "Unnamed user"}</strong>
                      <span className="table-subtext">
                        {member.email || "No email"}
                      </span>
                    </td>
                    <td>
                      <span className="role-label">{member.role}</span>
                    </td>
                    <td>
                      <StatusBadge
                        status={
                          member.status === "active"
                            ? "success"
                            : member.status === "suspended"
                              ? "danger"
                              : "warning"
                        }
                      >
                        {member.status}
                      </StatusBadge>
                    </td>
                    <td>
                      <select
                        className="table-select"
                        value={member.department_id || ""}
                        disabled={member.status !== "active"}
                        onChange={(event) =>
                          void changeDepartment(
                            member.user_id,
                            event.target.value
                          )
                        }
                      >
                        <option value="">Unassigned</option>
                        {departments.map((department) => (
                          <option key={department.id} value={department.id}>
                            {department.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      {new Date(member.joined_at).toLocaleDateString()}
                    </td>
                    <td>
                      
<div className="table-actions">
  {/* Role management */}
  <PermissionGate permission="members:update">
    {member.role !== "owner" && (
      <select
        className="table-select"
        value={member.role}
        onChange={(event) =>
          void changeRole(
            member.user_id,
            event.target.value as OrganizationRole
          )
        }
      >
        {isOwner && <option value="admin">Admin</option>}
        <option value="analyst">Analyst</option>
        <option value="reviewer">Reviewer</option>
      </select>
    )}
  </PermissionGate>

  {/* Department assignment */}
  <PermissionGate
    permission="members:update"
    fallback={
      <span className="table-subtext">
        {departments.find(
          (department) => department.id === member.department_id
        )?.name || "Unassigned"}
      </span>
    }
  >
    <select
      className="table-select"
      value={member.department_id || ""}
      disabled={member.status !== "active"}
      onChange={(event) =>
        void changeDepartment(
          member.user_id,
          event.target.value
        )
      }
    >
      <option value="">Unassigned</option>

      {departments.map((department) => (
        <option key={department.id} value={department.id}>
          {department.name}
        </option>
      ))}
    </select>
  </PermissionGate>

  {/* Membership status */}
  <PermissionGate permission="members:remove">
    {member.role !== "owner" && (
      <button
        type="button"
        className="small-action-button"
        onClick={() =>
          void changeStatus(
            member.user_id,
            member.status !== "active"
          )
        }
      >
        {member.status === "active" ? "Suspend" : "Activate"}
      </button>
    )}
  </PermissionGate>
</div>

                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
