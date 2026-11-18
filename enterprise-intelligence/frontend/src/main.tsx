
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { AppProviders } from "./app/providers";
import { ErrorBoundary } from "./components/ErrorBoundary";

import "./styles/globals.css";

ReactDOM.createRoot(
  document.getElementById("root")!
).render(
  <React.StrictMode>
    <ErrorBoundary>
    <AppProviders>
      <App />
    </AppProviders>
    </ErrorBoundary>
  </React.StrictMode>
);
