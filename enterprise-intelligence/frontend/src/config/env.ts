
const clean = (value: string | undefined) =>
  (value || "").trim().replace(/\/+$/, "");

export const env = {
  apiBaseUrl: clean(import.meta.env.VITE_API_BASE_URL),
  apiPrefix: "/api/v1",

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
