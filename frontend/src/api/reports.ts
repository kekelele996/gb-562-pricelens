import { http } from './client';
import type { AuditLog, Report } from '../types/models';

export const reportsApi = {
  daily: () => http.get<Report>('/reports/daily'),
  csv: () => http.text('/reports/daily.csv'),
  auditLogs: () => http.get<{ items: AuditLog[]; total: number }>('/audit-logs'),
};
