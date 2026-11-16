
import { ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";

export function AccessDeniedPage() {
  return (
    <div className="standalone-state">
      <div className="standalone-icon danger">
        <ShieldAlert size={28} />
      </div>
      <h1>Access denied</h1>
      <p>
        Your current organization role does not grant access to this area.
        Contact your organization administrator if you need access.
      </p>
      <Link className="primary-button" to="/dashboard">
        Return to dashboard
      </Link>
    </div>
  );
}
