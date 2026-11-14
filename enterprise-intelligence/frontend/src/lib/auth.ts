
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
  },

  isAuthenticated(): boolean {
    return Boolean(accessToken);
  }
};
