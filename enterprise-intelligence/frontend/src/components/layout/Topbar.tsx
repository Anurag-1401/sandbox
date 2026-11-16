
import {
  Bell,
  Building2,
  ChevronDown,
  LogOut,
  Search,
  UserRound
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import { useAuth } from "../../app/AuthProvider";
import { useWorkspace } from "../../app/WorkspaceProvider";

export function Topbar() {
  const navigate = useNavigate();

  const { user, logout } = useAuth();
  const { activeWorkspace } = useWorkspace();

  const displayName =
    user?.profile.name ||
    user?.profile.preferred_username ||
    user?.profile.email ||
    "Account";

  const email = user?.profile.email || "";

  return (
    <header className="topbar">
      <div className="topbar-context">
        <span className="breadcrumb-muted">Workspace</span>
        <span className="breadcrumb-divider">/</span>
        <span className="breadcrumb-current">
          {activeWorkspace?.name || "Overview"}
        </span>
      </div>

      <div className="topbar-actions">
        <div className="global-search">
          <Search size={16} />
          <span>Search intelligence...</span>
          <kbd>⌘ K</kbd>
        </div>

        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
          disabled
          title="Notifications will be connected in a later milestone"
        >
          <Bell size={19} />
        </button>

        <div className="topbar-divider" />

        <div className="profile-menu">
          <button
            className="profile-button"
            type="button"
            onClick={() => navigate("/profile")}
          >
            <div className="avatar">
              {displayName.slice(0, 1).toUpperCase()}
            </div>

            <div className="profile-copy">
              <span className="profile-name">{displayName}</span>
              <span className="profile-role">
                {activeWorkspace?.role || email}
              </span>
            </div>

            <ChevronDown size={15} />
          </button>

          <div className="profile-dropdown">
            <button
              type="button"
              onClick={() => navigate("/profile")}
            >
              <UserRound size={15} />
              My profile
            </button>

            <button
              type="button"
              onClick={() => navigate("/select-workspace")}
            >
              <Building2 size={15} />
              Switch workspace
            </button>

            <button
              type="button"
              onClick={() => void logout()}
            >
              <LogOut size={15} />
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
