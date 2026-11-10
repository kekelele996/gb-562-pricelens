import { http } from './client';
import type { PreviewOut, Template } from '../types/models';

export const templatesApi = {
  get: (id: number) => http.get<Template>(`/templates/${id}`),
  preview: (id: number, snapshotId?: number) =>
    http.get<PreviewOut>(`/templates/${id}/preview${snapshotId ? `?snapshot_id=${snapshotId}` : ''}`),
  update: (id: number, fieldRules: unknown[], changeNote?: string) =>
    http.patch<Template>(`/templates/${id}`, { field_rules: fieldRules, change_note: changeNote }),
};
