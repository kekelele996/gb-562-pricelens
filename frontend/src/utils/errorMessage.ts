const CODE_MESSAGE: Record<string, string> = {
  AUTH_INVALID: '邮箱或密码不正确',
  AUTH_MISSING: '登录已过期，请重新登录',
  FORBIDDEN: '当前角色无权执行该操作',
  NOT_FOUND: '对象不存在或已被归档',
  CONFLICT: '对象状态冲突，请刷新后重试',
  RATE_LIMITED: '操作过于频繁，请稍后再试',
  VALIDATION: '提交内容不合法',
  INTERNAL: '服务内部错误，请稍后重试',
};

export function errorMessage(payload: unknown, fallback = '请求失败'): string {
  if (!payload || typeof payload !== 'object') return fallback;
  const data = payload as { code?: string; message?: string; detail?: unknown };
  if (data.code && CODE_MESSAGE[data.code]) {
    return data.detail ? `${CODE_MESSAGE[data.code]}（${String(data.detail)}）` : CODE_MESSAGE[data.code];
  }
  return data.message || fallback;
}
