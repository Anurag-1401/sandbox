
import axios from "axios";

import { env } from "../config/env";
import { auth } from "./auth";
import { getActiveOrganizationId } from "./organization-context";

export const api = axios.create({
  baseURL: `${env.apiBaseUrl}${env.apiPrefix}`,
  timeout: 120_000,
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
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    }

    return Promise.reject(error);
  }
);

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (error.response?.status === 401) {
      return "Your session is not authenticated. Please sign in.";
    }

    if (error.response?.status === 403) {
      return "Your organization role does not allow this operation.";
    }

    if (error.response?.status === 404) {
      return "The requested document was not found.";
    }

    if (error.response?.status === 413) {
      return "The file exceeds the configured upload size limit.";
    }

    if (error.response?.status === 415) {
      return "This file type is not supported. Upload a PDF.";
    }

    if (error.response?.status === 422) {
      return typeof detail === "string"
        ? detail
        : "The document could not be validated or processed.";
    }

    if (!error.response) {
      return "Unable to connect to the backend. Check the API server.";
    }
  }

  return "An unexpected error occurred.";
}
