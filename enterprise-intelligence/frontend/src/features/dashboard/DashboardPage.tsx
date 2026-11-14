
import {
  ArrowUpRight,
  FileText,
  GitBranch,
  ShieldCheck,
  Workflow
} from "lucide-react";
import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";

const metrics = [
  {
    label: "Documents indexed",
    value: "—",
    note: "Awaiting live API integration",
    icon: FileText
  },
  {
    label: "Active investigations",
    value: "—",
    note: "Awaiting live API integration",
    icon: Workflow
  },
  {
    label: "Verified findings",
    value: "—",
    note: "Awaiting live API integration",
    icon: ShieldCheck
  },
  {
    label: "Knowledge graph nodes",
    value: "—",
    note: "Awaiting live API integration",
    icon: GitBranch
  }
];

export function DashboardPage() {
  return (
    <div className="dashboard-page">
      <PageHeader
        eyebrow="INTELLIGENCE OVERVIEW"
        title="Workspace overview"
        description="A consolidated view of your organization's intelligence operations."
      />

      <div className="welcome-panel">
        <div>
          <div className="welcome-kicker">ENTERPRISE INTELLIGENCE PLATFORM</div>
          <h2>Your intelligence workspace starts here.</h2>
          <p>
            Bring documents, regulatory information, investigations and
            verified evidence into one connected workspace.
          </p>
        </div>
        <div className="welcome-visual" aria-hidden="true">
          <div className="visual-ring ring-one" />
          <div className="visual-ring ring-two" />
          <div className="visual-core">
            <GitBranch size={32} />
          </div>
        </div>
      </div>

      <div className="section-heading">
        <div>
          <h2>Platform metrics</h2>
          <p>Live values will appear after backend integration.</p>
        </div>
        <StatusBadge status="neutral">Not connected</StatusBadge>
      </div>

      <div className="metric-grid">
        {metrics.map(({ label, value, note, icon: Icon }) => (
          <article className="metric-card" key={label}>
            <div className="metric-card-top">
              <span className="metric-icon"><Icon size={19} /></span>
              <ArrowUpRight size={16} className="metric-arrow" />
            </div>
            <div className="metric-value">{value}</div>
            <div className="metric-label">{label}</div>
            <div className="metric-note">{note}</div>
          </article>
        ))}
      </div>

      <div className="section-heading lower-heading">
        <div>
          <h2>Workspace activity</h2>
          <p>Activity feeds will be connected in later frontend milestones.</p>
        </div>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon"><Workflow size={22} /></div>
        <h3>No activity to display yet</h3>
        <p>
          Once the frontend is connected to your backend, recent document
          processing, investigation and verification activity will appear here.
        </p>
      </div>
    </div>
  );
}
