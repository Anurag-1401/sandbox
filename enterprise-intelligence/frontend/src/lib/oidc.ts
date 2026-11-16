
import {
  UserManager,
  WebStorageStateStore
} from "oidc-client-ts";

import { env, isOidcConfigured } from "../config/env";

export const oidcManager = isOidcConfigured
  ? new UserManager({
      authority: env.oidcAuthority,
      client_id: env.oidcClientId,
      redirect_uri: env.oidcRedirectUri,
      post_logout_redirect_uri: env.oidcPostLogoutRedirectUri,

      response_type: "code",
      scope: env.oidcScope,

      userStore: new WebStorageStateStore({
        store: window.sessionStorage
      }),

      automaticSilentRenew: false,
      monitorSession: false,
      loadUserInfo: true
    })
  : null;
