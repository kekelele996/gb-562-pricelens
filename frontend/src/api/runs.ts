import { http } from './client';
import type { Run, TrendPoint } from '../types/models';

export const runsApi = {
  list: (siteId?: number) =>
    http.get<{ items: Run[]; total: number; trend: TrendPoint[] }>(`/runs${siteId ? `?site_id=${siteId}` : ''}`),
  get: (id: number) => http.get<Run>(`/runs/${id}`),
  execute: (templateId: number, snapshotId: number) =>
    http.post<Run>('/runs', { template_id: templateId, snapshot_id: snapshotId }),
};
