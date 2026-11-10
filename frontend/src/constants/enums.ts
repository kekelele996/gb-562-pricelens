/** 前端共享枚举（后端 src/constants/enums.py 对应同一组值）。 */
import type { AlertStatus, FieldStatus, RunStatus, Severity, TemplateStatus } from '../types/models';

export const SEVERITY_LABEL: Record<Severity, string> = {
  high: '高危',
  medium: '关注',
  low: '观察',
  none: '正常',
};

export const ALERT_STATUS_LABEL: Record<AlertStatus, string> = {
  open: '待处置',
  accepted: '已接受',
  dismissed: '已驳回',
};

export const TEMPLATE_STATUS_LABEL: Record<TemplateStatus, string> = {
  draft: '草稿',
  active: '生效中',
  deprecated: '已归档',
};

export const RUN_STATUS_LABEL: Record<RunStatus, string> = {
  queued: '排队中',
  running: '执行中',
  success: '成功',
  failed: '失败',
};

export const FIELD_STATUS_LABEL: Record<FieldStatus, string> = {
  hit: '命中',
  wrong: '错位',
  miss: '缺失',
};

export const CANDIDATE_KIND_LABEL: Record<string, string> = {
  class_relaxed: 'class 容错变体',
  sibling_index: '兄弟索引',
  text_anchor: '文本锚点 XPath',
  fuzzy_text: 'tag + 文本模糊',
  existing: '现行规则',
};

export const DRIFT_WEIGHTS = [
  { key: 'path_jaccard', label: '结构路径 Jaccard', weight: 0.4, inverted: true },
  { key: 'node_ratio_delta', label: '节点数变化率', weight: 0.2, inverted: false },
  { key: 'text_similarity', label: '正文本相似度', weight: 0.2, inverted: true },
  { key: 'field_miss_delta', label: '字段命中率下降', weight: 0.2, inverted: false },
];
