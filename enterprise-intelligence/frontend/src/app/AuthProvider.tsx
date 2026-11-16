
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";

import type { User } from "oidc-client-ts";

import { isOidcConfigured } from "../config/env";
import { auth } from "../lib/auth";
import { oidcManager } from "../lib/oidc";

type AuthStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "unconfigured";

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>(
    isOidcConfigured ? "loading" : "unconfigured"
  );

  const acceptUser = useCallback((nextUser: User | null) => {
    if (!nextUser || nextUser.expired || !nextUser.access_token) {
      auth.clear();
      setUser(null);
      setStatus("unauthenticated");
      return;
    }

    auth.setAccessToken(nextUser.access_token);
    setUser(nextUser);
    setStatus("authenticated");
  }, []);

  
useEffect(() => {
  const manager = oidcManager;

  if (!manager) {
    auth.clear();
    setStatus("unconfigured");
    return;
  }

  let mounted = true;

  const onUserLoaded = (nextUser: User) => {
    if (mounted) {
      acceptUser(nextUser);
    }
  };

  const onUserUnloaded = () => {
    if (mounted) {
      acceptUser(null);
    }
  };

  const onTokenExpired = async () => {
    try {
      await manager.removeUser();
    } catch (error) {
      console.error("Failed to remove expired OIDC user:", error);
    }

    if (mounted) {
      acceptUser(null);
    }
  };

  const onUnauthorized = async () => {
    try {
      await manager.removeUser();
    } catch (error) {
      console.error("Failed to remove unauthorized OIDC user:", error);
    }

    if (mounted) {
      acceptUser(null);
    }
  };

  manager.events.addUserLoaded(onUserLoaded);
  manager.events.addUserUnloaded(onUserUnloaded);
  manager.events.addAccessTokenExpired(onTokenExpired);

  window.addEventListener("auth:unauthorized", onUnauthorized);

  manager
    .getUser()
    .then((existingUser) => {
      if (mounted) {
        acceptUser(existingUser);
      }
    })
    .catch((error) => {
      console.error("Failed to restore OIDC session:", error);

      if (mounted) {
        auth.clear();
        setStatus("unauthenticated");
      }
    });

  return () => {
    mounted = false;

    manager.events.removeUserLoaded(onUserLoaded);
    manager.events.removeUserUnloaded(onUserUnloaded);
    manager.events.removeAccessTokenExpired(onTokenExpired);

    window.removeEventListener("auth:unauthorized", onUnauthorized);
  };
}, [acceptUser]);


  const login = useCallback(async () => {
    if (!oidcManager) {
      throw new Error("OIDC is not configured.");
    }

    await oidcManager.signinRedirect();
  }, []);

  const logout = useCallback(async () => {
    auth.clear();

    if (!oidcManager) {
      setUser(null);
      setStatus("unauthenticated");
      return;
    }

    await oidcManager.signoutRedirect({
      id_token_hint: user?.id_token
    });
  }, [user]);

  const value = useMemo(
    () => ({ status, user, login, logout }),
    [status, user, login, logout]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
