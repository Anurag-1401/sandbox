const ORGANIZATION_STORAGE_KEY = "ei.activeOrganizationId";

export const organizationContext = {
  getOrganizationId(): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    return window.sessionStorage.getItem(ORGANIZATION_STORAGE_KEY);
  },

  setOrganizationId(id: string | null): void {
    if (typeof window === "undefined") {
      return;
    }

    const normalizedId = id?.trim();

    if (!normalizedId) {
      window.sessionStorage.removeItem(ORGANIZATION_STORAGE_KEY);
      return;
    }

    window.sessionStorage.setItem(
      ORGANIZATION_STORAGE_KEY,
      normalizedId
    );
  },

  clear(): void {
    if (typeof window === "undefined") {
      return;
    }

    window.sessionStorage.removeItem(ORGANIZATION_STORAGE_KEY);
  }
};