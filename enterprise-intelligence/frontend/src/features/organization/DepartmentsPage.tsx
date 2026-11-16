import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Building2, Plus } from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { PermissionGate } from "../../app/PermissionGate";
import {
  enterpriseApi,
  type Department
} from "../../lib/enterprise-api";
import { getApiErrorMessage } from "../../lib/api";

export function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDepartments() {
    setLoading(true);
    setError(null);

    try {
      setDepartments(await enterpriseApi.getDepartments());
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDepartments();
  }, []);

  async function createDepartment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await enterpriseApi.createDepartment({
        name,
        description: description || null
      });

      setName("");
      setDescription("");
      await loadDepartments();
    } catch (cause) {
      setError(getApiErrorMessage(cause));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="ORGANIZATION MANAGEMENT"
        title="Departments"
        description="Organize members into departments within the active organization."
      />

      {error && <div className="form-alert error">{error}</div>}

      <PermissionGate permission="departments:manage">
        <div className="settings-card">
          <div className="settings-card-heading">
            <div className="settings-card-icon"><Plus size={20} /></div>
            <div>
              <h2>Create department</h2>
              <p>Add a department to the active workspace.</p>
            </div>
          </div>

          <form className="settings-form" onSubmit={createDepartment}>
            <div className="form-field">
              <label htmlFor="departmentName">Department name</label>
              <input
                id="departmentName"
                value={name}
                onChange={(event) => setName(event.target.value)}
                minLength={2}
                maxLength={120}
                required
                placeholder="e.g. Compliance"
              />
            </div>

            <div className="form-field">
              <label htmlFor="departmentDescription">Description</label>
              <textarea
                id="departmentDescription"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                maxLength={2000}
                rows={3}
                placeholder="Department responsibilities..."
              />
            </div>

            <button className="primary-button" disabled={saving}>
              {saving ? "Creating..." : "Create department"}
            </button>
          </form>
        </div>
      </PermissionGate>

      <div className="department-grid">
        {loading ? (
          <div className="page-loading">Loading departments...</div>
        ) : departments.length === 0 ? (
          <div className="empty-state compact">
            <h3>No departments found</h3>
            <p>Create a department if your role permits it.</p>
          </div>
        ) : (
          departments.map((department) => (
            <article className="department-card" key={department.id}>
              <div className="department-card-icon">
                <Building2 size={19} />
              </div>
              <h3>{department.name}</h3>
              <p>{department.description || "No description provided."}</p>
              <span>
                Created {new Date(department.created_at).toLocaleDateString()}
              </span>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
