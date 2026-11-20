
import axios from "axios";

import { env } from "../config/env";
import { auth } from "./auth";
import { getActiveOrganizationId } from "./workspace-context";

export const api = axios.create({
  baseURL: `${env.apiBaseUrl}${env.apiPrefix}`,
  timeout: 60_000,
  headers: {
    Accept: "application/json"
  }
});

api.interceptors.request.use((config) => {
  const token = auth.getAccessToken();
const organizationId = getActiveOrganizationId();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (organizationId) {
    config.headers["X-Organization-ID"] = organizationId;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      auth.clear();

      window.dispatchEvent(
        new CustomEvent("auth:unauthorized")
      );
    }

    if (error.response?.status === 403) {
      window.dispatchEvent(
        new CustomEvent("auth:forbidden", {
          detail: error.response.data
        })
      );
    }

    return Promise.reject(error);
  }
);

function normalizeValidationErrors(detail: unknown): string | null {
  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail
    .map((item) => {
      if (
        item &&
        typeof item === "object" &&
        "msg" in item &&
        typeof item.msg === "string"
      ) {
        const location =
          "loc" in item && Array.isArray(item.loc)
            ? item.loc.filter((part:any) => part !== "body").join(".")
            : "";

        return location
          ? `${location}: ${item.msg}`
          : item.msg;
      }

      return null;
    })
    .filter((item): item is string => Boolean(item));

  return messages.length ? messages.join("; ") : null;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    const validationMessage = normalizeValidationErrors(detail);

    if (validationMessage) {
      return validationMessage;
    }

    if (status === 401) {
      return "Your session is not authenticated. Please sign in again.";
    }

    if (status === 403) {
      return "You do not have permission to perform this action.";
    }

    if (status === 404) {
      return "The requested resource could not be found.";
    }

    if (status === 409) {
      return "This operation conflicts with the current resource state.";
    }

    if (status === 422) {
      return "The submitted information is invalid. Check the fields and try again.";
    }

    if (status && status >= 500) {
      return "The server encountered an error. Please try again later.";
    }

    if (!error.response) {
      return "Unable to connect to the backend. Check the API server and network.";
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred.";
}
