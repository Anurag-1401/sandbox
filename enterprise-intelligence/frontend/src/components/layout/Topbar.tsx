
import { Bell, ChevronDown, Command, Search } from "lucide-react";

export function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-context">
        <span className="breadcrumb-muted">Workspace</span>
        <span className="breadcrumb-divider">/</span>
        <span className="breadcrumb-current">Overview</span>
      </div>

      <div className="topbar-actions">
        <button className="global-search" type="button" disabled>
          <Search size={16} />
          <span>Search intelligence...</span>
          <kbd><Command size={11} /> K</kbd>
        </button>

        <button
          className="icon-button"
          type="button"
          aria-label="Notifications"
          disabled
        >
          <Bell size={19} />
          <span className="notification-dot" />
        </button>

        <div className="topbar-divider" />

        <button className="profile-button" type="button" disabled>
          <div className="avatar">EI</div>
          <div className="profile-copy">
            <span className="profile-name">Workspace User</span>
            <span className="profile-role">Not signed in</span>
          </div>
          <ChevronDown size={15} />
        </button>
      </div>
    </header>
  );
}
