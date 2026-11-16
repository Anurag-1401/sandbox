
import {
  Activity,
  BookOpen,
  BrainCircuit,
  FileSearch,
  Files,
  GitBranch,
  LayoutDashboard,
  Network,
  ShieldCheck,
  Workflow
} from "lucide-react";

import { NavLink } from "react-router-dom";

const groups = [
  {
    title: "WORKSPACE",
    items: [
      {
        label: "Dashboard",
        path: "/dashboard",
        icon: LayoutDashboard
      },
      {
        label: "Documents",
        path: "/documents",
        icon: Files
      },
      {
        label: "Search",
        path: "/search",
        icon: FileSearch
      },
      {
        label: "AI Research",
        path: "/research",
        icon: BrainCircuit
      }
    ]
  },
  {
    title: "INTELLIGENCE",
    items: [
      {
        label: "Investigations",
        path: "/investigations",
        icon: Workflow
      },
      {
        label: "Verification",
        path: "/verification",
        icon: ShieldCheck
      },
      {
        label: "Regulatory Updates",
        path: "/regulatory",
        icon: Activity
      },
      {
        label: "Knowledge Graph",
        path: "/knowledge-graph",
        icon: Network
      },
      {
        label: "Impact Analysis",
        path: "/impact-analysis",
        icon: GitBranch
      }
    ]
  },
  {
    title: "KNOWLEDGE",
    items: [
      {
        label: "Knowledge Library",
        path: "/knowledge-library",
        icon: BookOpen
      }
    ]
  }
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">EI</div>

        <div>
          <div className="brand-name">Enterprise</div>
          <div className="brand-subtitle">INTELLIGENCE</div>
        </div>
      </div>

      <div className="workspace-label">
        PLATFORM WORKSPACE
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {groups.map((group) => (
          <div className="nav-group" key={group.title}>
            <div className="nav-section-title">
              {group.title}
            </div>

            {group.items.map(({ label, path, icon: Icon }) => (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
              >
                <Icon size={18} strokeWidth={1.8} />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="system-indicator" />

        <div>
          <div className="system-title">Platform workspace</div>
          <div className="system-subtitle">Document intelligence</div>
        </div>
      </div>
    </aside>
  );
}
