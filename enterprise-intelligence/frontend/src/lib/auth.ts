import { organizationContext } from "./organization-context";

let accessToken: string | null = null;

export const auth = {
  getAccessToken(): string | null {
    return accessToken;
  },

  setAccessToken(token: string | null): void {
    accessToken = token;
  },

  clear(): void {
    accessToken = null;
    organizationContext.clear();
  },

  isAuthenticated(): boolean {
    return Boolean(accessToken);
  }
};
