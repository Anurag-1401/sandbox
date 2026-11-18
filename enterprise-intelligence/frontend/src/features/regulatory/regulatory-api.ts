
import { api } from "../../lib/api";

export type AlertStatus = "pending" | "reviewed" | "dismissed";

export type ApplicabilityDecision =
  | "applicable"
  | "not_applicable"
  | "uncertain";

export type AlertSeverity = "info" | "low" | "medium" | "high";

export interface RegulatorySource {
  id: string;
  code: string;
  name: string;
  authority: string;
  jurisdiction: string;
  source_type: "rss" | "atom" | "html";
  scan_interval_minutes: number;
}

export interface RegulatorySubscription {
  id: string;
  source_id: string;
  filters: {
    industries?: string[];
    products?: string[];
    jurisdictions?: string[];
    keywords?: string[];
  };
  active: boolean;
  created_at: string;
}

export interface SubscriptionCreateRequest {
  source_id: string;
  filters: {
    industries?: string[];
    products?: string[];
    jurisdictions?: string[];
    keywords?: string[];
  };
}

export interface RegulatoryAlert {
  id: string;
  organization_id: string;
  publication_id: string;
  publication_version_id: string;
  document_id: string | null;
  alert_type: string;
  severity: AlertSeverity;
  relevance_status: string;
  status: AlertStatus;
  title: string;
  summary: string;
  matched_terms: Array<{
    filter: string;
    term: string;
  }>;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
}

export interface RegulatoryPublication {
  id: string;
  title: string;
  canonical_url: string;
  published_at: string | null;
  effective_at: string | null;
  current_version_number: number;
}

export interface RegulatoryPublicationVersion {
  id: string;
  version_number: number;
  content_hash: string;
  diff_summary: {
    method?: string;
    previous_line_count?: number;
    current_line_count?: number;
    added_line_count?: number;
    removed_line_count?: number;
    changed?: boolean;
    added_excerpt?: string[];
    removed_excerpt?: string[];
    limitations?: string[];
    [key: string]: unknown;
  };
  observed_at: string;
}

export interface RegulatoryAlertDetail {
  alert: RegulatoryAlert;
  publication: RegulatoryPublication;
  version: RegulatoryPublicationVersion;
}

export interface AlertReviewRequest {
  status: "reviewed" | "dismissed";
  notes?: string | null;
  applicability_decision?: ApplicabilityDecision | null;
  effective_at?: string | null;
}

export interface AlertReviewResponse {
  alert_id: string;
  status: AlertStatus;
  reviewed_by: string;
  reviewed_at: string;
}

const BASE = "/regulatory";

export async function getRegulatorySources(): Promise<RegulatorySource[]> {
  const response = await api.get<RegulatorySource[]>(
    `${BASE}/sources`
  );

  return response.data;
}

export async function getRegulatorySubscriptions(): Promise<
  RegulatorySubscription[]
> {
  const response = await api.get<RegulatorySubscription[]>(
    `${BASE}/subscriptions`
  );

  return response.data;
}

export async function createRegulatorySubscription(
  payload: SubscriptionCreateRequest
): Promise<RegulatorySubscription> {
  const response = await api.post<RegulatorySubscription>(
    `${BASE}/subscriptions`,
    payload
  );

  return response.data;
}

export async function deactivateRegulatorySubscription(
  subscriptionId: string
): Promise<{ subscription_id: string; active: boolean }> {
  const response = await api.delete<{
    subscription_id: string;
    active: boolean;
  }>(`${BASE}/subscriptions/${subscriptionId}`);

  return response.data;
}

export async function getRegulatoryAlerts(
  status?: AlertStatus,
  limit = 100,
  offset = 0
): Promise<RegulatoryAlert[]> {
  const response = await api.get<RegulatoryAlert[]>(
    `${BASE}/alerts`,
    {
      params: {
        status,
        limit,
        offset
      }
    }
  );

  return response.data;
}

export async function getRegulatoryAlert(
  alertId: string
): Promise<RegulatoryAlertDetail> {
  const response = await api.get<RegulatoryAlertDetail>(
    `${BASE}/alerts/${alertId}`
  );

  return response.data;
}

export async function reviewRegulatoryAlert(
  alertId: string,
  payload: AlertReviewRequest
): Promise<AlertReviewResponse> {
  const response = await api.patch<AlertReviewResponse>(
    `${BASE}/alerts/${alertId}`,
    payload
  );

  return response.data;
}

export async function getPublicationVersions(
  publicationId: string
): Promise<RegulatoryPublicationVersion[]> {
  const response = await api.get<RegulatoryPublicationVersion[]>(
    `${BASE}/publications/${publicationId}/versions`
  );

  return response.data;
}
