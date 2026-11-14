
import axios from "axios";
import { env } from "../config/env";
import { auth } from "./auth";

export const api = axios.create({
  baseURL: `${env.apiBaseUrl}${env.apiPrefix}`,
  timeout: 60_000,
  headers: {
    Accept: "application/json"
  }
});

api.interceptors.request.use((config) => {
  const token = auth.getAccessToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
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
    if (!error.response) {
      return "Unable to connect to the backend. Check the API server.";
    }
  }

  return "An unexpected error occurred.";
}
