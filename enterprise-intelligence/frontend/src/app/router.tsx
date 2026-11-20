import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { ProtectedRoute } from "./ProtectedRoute";

import { LoginPage } from "../features/auth/LoginPage";
import { AuthCallbackPage } from "../features/auth/AuthCallbackPage";
import { AccessDeniedPage } from "../features/auth/AccessDeniedPage";

import { WorkspaceSelectPage } from "../features/organization/WorkspaceSelectPage";
import { TeamPage } from "../features/organization/TeamPage";
import { DepartmentsPage } from "../features/organization/DepartmentsPage";
import { WorkspaceSettingsPage } from "../features/organization/WorkspaceSettingsPage";
import { AuditLogsPage } from "../features/organization/AuditLogsPage";
import { ProfilePage } from "../features/profile/ProfilePage";

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
  // Public authentication routes
  {
    path: "/login",
    element: <LoginPage />
  },
  {
    path: "/auth/callback",
    element: <AuthCallbackPage />
  },

  // Authenticated users can select or change their workspace.
  // This route deliberately does not require an active workspace.
  {
    path: "/select-workspace",
    element: (
      <ProtectedRoute requireWorkspace={false}>
        <WorkspaceSelectPage />
      </ProtectedRoute>
    )
  },

  {
    path: "/access-denied",
    element: <AccessDeniedPage />
  },

  // All application pages require an authenticated user
  // and an active organization context.
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },

      // Core workspace
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

      // Investigations and verification
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

      // Regulatory intelligence
      {
        path: "regulatory",
        element: <RegulatoryPage />
      },
      {
        path: "regulatory/alerts/:alertId",
        element: <RegulatoryAlertDetailPage />
      },

      // Knowledge graph and impact analysis
      {
        path: "knowledge-graph",
        element: <KnowledgeGraphPage />
      },
      {
        path: "impact-analysis",
        element: <ImpactAnalysisPage />
      },

      // Organization administration
      {
        path: "organization/team",
        element: <TeamPage />
      },
      {
        path: "organization/departments",
        element: <DepartmentsPage />
      },
      {
        path: "organization/settings",
        element: <WorkspaceSettingsPage />
      },
      {
        path: "organization/audit-logs",
        element: <AuditLogsPage />
      },

      // User account
      {
        path: "profile",
        element: <ProfilePage />
      },

      // There is no separate Knowledge Library page in this archive.
      // Documents is the existing indexed knowledge library.
      {
        path: "knowledge-library",
        element: <Navigate to="/documents" replace />
      },

      {
        path: "*",
        element: <Navigate to="/dashboard" replace />
      }
    ]
  }
]);