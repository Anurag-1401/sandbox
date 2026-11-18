
import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";

import { DashboardPage } from "../features/dashboard/DashboardPage";

import { DocumentsPage } from "../features/documents/DocumentsPage";
import { DocumentDetailPage } from "../features/documents/DocumentsDetailPage";

import { SearchPage } from "../features/search/SearchPage";
import { ResearchPage } from "../features/research/ResearchPage";

import { InvestigationsPage } from "../features/investigations/InvestigationsPage";
import { InvestigationDetailPage } from "../features/investigations/InvestigatioDetailPage";
import { VerificationPage } from "../features/verification/VerificationPage";

import { RegulatoryPage } from "../features/regulatory/RegulatoryPage";
import { RegulatoryAlertDetailPage } from "../features/regulatory/RegulatoryAlertDetailPage";

import { KnowledgeGraphPage } from "../features/knowledge-graph/KnowledgeGraphPage";
import { ImpactAnalysisPage } from "../features/impact-analysis/ImpactAnalysisPage";

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
      },
      {
        path: "investigations",
        element: <InvestigationsPage />
      },
      {
        path: "investigations/:investigationId",
        element: <InvestigationDetailPage />
      },
      {
        path: "verification",
        element: <VerificationPage />
      },
      {
        path: "regulatory",
        element: <RegulatoryPage />
      },
      {
        path: "regulatory/alerts/:alertId",
        element: <RegulatoryAlertDetailPage />
      },
      {
        path: "knowledge-graph",
        element: <KnowledgeGraphPage />
      },
      {
        path: "impact-analysis",
        element: <ImpactAnalysisPage />
      }
    ]
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />
  }
]);
