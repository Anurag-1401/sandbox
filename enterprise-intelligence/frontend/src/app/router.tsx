
import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { DocumentsPage } from "../features/documents/DocumentsPage";
import { DocumentDetailPage } from "../features/documents/DocumentsDetailPage";
import { SearchPage } from "../features/search/SearchPage";
import { ResearchPage } from "../features/research/ResearchPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: "dashboard",
        element: <DashboardPage />
      },
      {
        path: "documents",
        element: <DocumentsPage />
      },
      {
        path: "documents/:documentId",
        element: <DocumentDetailPage />
      },
      {
        path: "search",
        element: <SearchPage />
      },
      {
        path: "research",
        element: <ResearchPage />
      }
    ]
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />
  }
]);
