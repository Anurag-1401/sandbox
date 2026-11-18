
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

if (import.meta.env.PROD && !configuredApiBaseUrl) {
  throw new Error(
    "VITE_API_BASE_URL must be configured for production."
  );
}

const apiBaseUrl = (
  configuredApiBaseUrl || "http://localhost:8000"
).replace(/\/+$/, "");

const clean = (value: string | undefined) =>
  (value || "").trim().replace(/\/+$/, "");

export const env = {
  apiBaseUrl,
  apiPrefix: "/api/v1",

  authEnabled: import.meta.env.VITE_AUTH_ENABLED === "true",
  isProduction: import.meta.env.PROD,

  oidcAuthority: clean(import.meta.env.VITE_OIDC_AUTHORITY),
  oidcClientId: clean(import.meta.env.VITE_OIDC_CLIENT_ID),

  oidcRedirectUri:
    import.meta.env.VITE_OIDC_REDIRECT_URI ||
    `${window.location.origin}/auth/callback`,

  oidcPostLogoutRedirectUri:
    import.meta.env.VITE_OIDC_POST_LOGOUT_REDIRECT_URI ||
    `${window.location.origin}/login`,

  oidcScope:
    import.meta.env.VITE_OIDC_SCOPE || "openid profile email",

  defaultOrganizationId: clean(
    import.meta.env.VITE_DEFAULT_ORGANIZATION_ID
  )
} as const;

export const isOidcConfigured = Boolean(
  env.oidcAuthority &&
  env.oidcClientId &&
  env.oidcRedirectUri
);
