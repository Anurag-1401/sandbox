
import type { ReactNode } from "react";

type Status = "success" | "warning" | "danger" | "neutral" | "info";

interface StatusBadgeProps {
  status: Status;
  children: ReactNode;
}

export function StatusBadge({ status, children }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-${status}`}>
      <span className="status-dot" />
      {children}
    </span>
  );
}
