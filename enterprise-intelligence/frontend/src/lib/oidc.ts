import {
  UserManager,
  WebStorageStateStore
} from "oidc-client-ts";

import { env, isOidcConfigured } from "../config/env";

if (
  isOidcConfigured &&
  !env.oidcAudience
) {
  throw new Error(
    "VITE_OIDC_AUDIENCE must be configured for API authentication."
  );
}

export const oidcManager = isOidcConfigured
  ? new UserManager({
      authority: env.oidcAuthority,
      client_id: env.oidcClientId,

      redirect_uri: env.oidcRedirectUri,

      post_logout_redirect_uri:
        env.oidcPostLogoutRedirectUri,

      response_type: "code",

      scope: env.oidcScope,

      // Request an access token specifically for the backend API.
      extraQueryParams: {
        audience: env.oidcAudience
      },

      userStore: new WebStorageStateStore({
        store: window.sessionStorage
      }),

      automaticSilentRenew: false,

      monitorSession: false,

      loadUserInfo: false
    })
  : null;