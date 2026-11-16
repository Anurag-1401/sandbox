
import { env } from "../config/env";

const STORAGE_KEY = "ei.activeOrganizationId";

export function getActiveOrganizationId(): string | null {
  if (typeof window === "undefined") return null;

  return (
    window.sessionStorage.getItem(STORAGE_KEY) ||
    env.defaultOrganizationId ||
    null
  );
}

export function setActiveOrganizationId(id: string): void {
  window.sessionStorage.setItem(STORAGE_KEY, id);
}

export function clearActiveOrganizationId(): void {
  window.sessionStorage.removeItem(STORAGE_KEY);
}
