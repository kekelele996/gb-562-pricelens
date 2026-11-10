import { http } from './client';
import type { Alert, Snapshot } from '../types/models';

export const snapshotsApi = {
  list: (siteId?: number) =>
    http.get<{ items: Snapshot[]; total: number }>(`/snapshots${siteId ? `?site_id=${siteId}` : ''}`),
  get: (id: number) => http.get<Snapshot & { baseline: Snapshot | null }>(`/snapshots/${id}`),
  diagnose: (snapshotId: number, templateId: number) =>
    http.post<Alert>(`/snapshots/${snapshotId}/diagnose`, { template_id: templateId }),
};
