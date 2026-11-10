import { http } from './client';
import type { Alert, SuggestedPatch, Template } from '../types/models';

export const alertsApi = {
  list: (status?: string) =>
    http.get<{ items: Alert[]; total: number; open_count: number }>(`/alerts${status ? `?status=${status}` : ''}`),
  get: (id: number) => http.get<Alert>(`/alerts/${id}`),
  candidates: (id: number) =>
    http.post<{ alert: Alert; suggested_patch: SuggestedPatch }>(`/alerts/${id}/candidates`),
  changeStatus: (id: number, status: 'accepted' | 'dismissed', note?: string) =>
    http.post<{ id: number; status: string; audit_added: number }>(`/alerts/${id}/status`, { status, note }),
  apply: (id: number) =>
    http.post<{ template: Template; source_alert: number; audit_added: number }>(`/alerts/${id}/apply`),
};
