
const ORGANIZATION_STORAGE_KEY = "ei.activeOrganizationId";

export function getActiveOrganizationId(): string | null {
  if (typeof window === "undefined") return null;

  return window.sessionStorage.getItem(ORGANIZATION_STORAGE_KEY);
}

export function setActiveOrganizationId(id: string): void {
  window.sessionStorage.setItem(ORGANIZATION_STORAGE_KEY, id);
}

export function clearActiveOrganizationId(): void {
  window.sessionStorage.removeItem(ORGANIZATION_STORAGE_KEY);
}
