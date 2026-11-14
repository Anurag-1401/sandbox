
const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export const env = {
  apiBaseUrl,
  apiPrefix: "/api/v1",
  authEnabled: import.meta.env.VITE_AUTH_ENABLED === "true"
} as const;
