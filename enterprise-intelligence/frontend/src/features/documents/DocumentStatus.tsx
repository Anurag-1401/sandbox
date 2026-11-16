
import { StatusBadge } from "../../components/ui/StatusBadge";

export function DocumentStatus({
  status
}: {
  status: string;
}) {
  const normalized = status.toLowerCase();

  if (normalized === "indexed") {
    return <StatusBadge status="success">Indexed</StatusBadge>;
  }

  if (normalized === "processing") {
    return <StatusBadge status="warning">Processing</StatusBadge>;
  }

  if (normalized === "failed") {
    return <StatusBadge status="danger">Failed</StatusBadge>;
  }

  return <StatusBadge status="neutral">{status}</StatusBadge>;
}
