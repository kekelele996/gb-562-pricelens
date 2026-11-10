import { http } from './client';
import type { Site } from '../types/models';

export interface OverviewData {
  sites: number;
  active_sites: number;
  templates: number;
  active_templates: number;
  open_alerts: number;
  severity_counts: Record<string, number>;
}

export const sitesApi = {
  list: () => http.get<{ items: Site[]; total: number }>('/sites'),
  overview: () => http.get<OverviewData>('/sites/overview'),
  create: (payload: Record<string, unknown>) => http.post<{ id: number }>('/sites', payload),
};
