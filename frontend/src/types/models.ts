export type Role = 'admin' | 'analyst' | 'client';

export interface UserInfo {
  id: number;
  email: string;
  display_name: string;
  role: Role;
  role_label: string;
}

export type Severity = 'high' | 'medium' | 'low' | 'none';
export type AlertStatus = 'open' | 'accepted' | 'dismissed';
export type TemplateStatus = 'draft' | 'active' | 'deprecated';
export type RunStatus = 'queued' | 'running' | 'success' | 'failed';
export type FieldStatus = 'hit' | 'wrong' | 'miss';

export interface TemplateBrief {
  id: number;
  name: string;
  version: number;
  status: TemplateStatus;
  coverage_score: number;
  field_count: number;
}

export interface Site {
  id: number;
  name: string;
  domain: string;
  market: string;
  robots_policy: 'allow' | 'partial' | 'blocked';
  qps_limit: number;
  status: 'active' | 'paused';
  note?: string | null;
  alert_count: number;
  last_crawled_at: string | null;
  templates: TemplateBrief[];
}

export interface FieldRule {
  field: string;
  label: string;
  type: 'text' | 'price' | 'count' | 'stock';
  selector_candidates: string[];
  post_regex?: string | null;
  verified_value?: string | null;
  anchor_text?: string | null;
  patched?: boolean | null;
  patch_note?: string | null;
}

export interface Template {
  id: number;
  site_id: number;
  site_name: string;
  name: string;
  version: number;
  status: TemplateStatus;
  coverage_score: number;
  field_count: number;
  last_verified_at: string | null;
  change_note: string | null;
  field_rules: FieldRule[];
}

export interface FieldResult {
  field: string;
  label: string;
  type: string;
  value: string | null;
  raw: string | null;
  status: FieldStatus;
  similarity: number;
  matched_selector: string | null;
  snippet: string | null;
}

export interface PreviewOut {
  template_id: number;
  template_version: number;
  snapshot_id: number;
  snapshot_label: string;
  hits: number;
  total: number;
  fields: FieldResult[];
}

export interface Snapshot {
  id: number;
  site_id: number;
  site_name: string;
  domain: string;
  url: string;
  label: string;
  captured_at: string;
  dom_hash: string;
  byte_size: number;
  is_baseline: boolean;
}

export interface FieldMatrixRow {
  field: string;
  label: string;
  baseline_value: string | null;
  baseline_status: FieldStatus;
  new_value: string | null;
  new_status: FieldStatus;
  similarity: number;
  matched_selector: string | null;
}

export interface Diagnosis {
  status: string;
  drift_score: number;
  severity: Severity;
  components: Record<string, number>;
  top_changed_subtrees: { path: string; added: number; removed: number }[];
  reason_codes: string[];
  field_matrix: FieldMatrixRow[];
  affected_fields: string[];
  baseline_snapshot_id?: number;
  baseline_missing?: boolean;
  reason?: string;
}

export interface Candidate {
  kind: string;
  selector: string;
  value: string | null;
  hit_count: number;
  value_similarity: number;
  stability: number;
  specificity: number;
  hit_penalty: number;
  score: number;
  auto_applyable: boolean;
}

export interface HealField {
  field: string;
  label: string;
  needs_repair: boolean;
  current_status: FieldStatus;
  current_value: string | null;
  verified_value: string | null;
  stability: number;
  history_runs: number;
  candidates: Candidate[];
  selected: string | null;
  confidence: number;
  reason: string | null;
}

export interface SuggestedPatch {
  patch: Record<string, string>;
  fields: HealField[];
  threshold: number;
  auto_apply_count: number;
}

export interface Alert {
  id: number;
  site_id: number;
  site_name: string;
  snapshot_id: number;
  template_id: number | null;
  template_name: string | null;
  template_version?: number | null;
  drift_score: number;
  severity: Severity;
  status: AlertStatus;
  handled_by: string | null;
  handle_note: string | null;
  created_at: string;
  diagnosis: Diagnosis;
  suggested_patch: SuggestedPatch;
}

export interface Run {
  id: number;
  template_id: number;
  template_name: string;
  template_version: number;
  site_id: number;
  site_name: string;
  snapshot_id: number;
  status: RunStatus;
  hit_fields: number;
  missing_fields: number;
  f1_score: number | null;
  duration_ms: number;
  triggered_by: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
  field_results: FieldResult[];
}

export interface TrendPoint {
  run_id: number;
  site_name: string;
  version: number;
  f1_score: number | null;
  created_at: string;
  status: RunStatus;
}

export interface ReportRow {
  site_id: number;
  site_name: string;
  domain: string;
  snapshot_label: string;
  captured_at: string;
  title: string | null;
  list_price: string | null;
  promo_price: string | null;
  stock: string | null;
  f1_score: number | null;
  status: RunStatus;
}

export interface Report {
  generated_at: string;
  rows: ReportRow[];
  avg_f1: number | null;
}

export interface AuditLog {
  id: number;
  actor_email: string;
  actor_role: string;
  action: string;
  action_label?: string;
  entity: string;
  entity_id: string | null;
  detail: Record<string, unknown>;
  layer: string;
  created_at: string;
}
