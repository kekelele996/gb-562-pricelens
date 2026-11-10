import { useAsync } from '../hooks/useAsync';
import { reportsApi } from '../api/reports';
import StatusPill from '../components/common/StatusPill';
import { fmtDateTime } from '../utils/format';
import { RUN_STATUS_LABEL } from '../constants/enums';
import { uiStore } from '../stores/uiStore';

export default function ClientReport() {
  const { data, loading, error } = useAsync(() => reportsApi.daily(), []);

  async function download() {
    try {
      const csv = await reportsApi.csv();
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'pricelens-daily-report.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      uiStore.push('ok', `CSV 已导出（${csv.trim().split('\n').length} 行，含表头）`);
    } catch {
      uiStore.push('error', '导出失败，请稍后重试');
    }
  }

  if (error) return <div className="banner error">日报加载失败。</div>;
  if (loading && !data) return <div className="main">正在生成客户日报 …</div>;

  const rows = data?.rows ?? [];
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Daily / 客户只读</div>
          <h1>品牌客户价格日报</h1>
          <p className="sub">
            只读视图 · 生成于 {fmtDateTime(data?.generated_at)} · 6 个站点最新成功批次的字段快照
          </p>
        </div>
        <div className="head-actions">
          <StatusPill tone="active" label="READ ONLY" />
          <button className="btn btn-primary" onClick={download} data-testid="export-csv">
            导出 CSV
          </button>
        </div>
      </div>

      <div className="metrics">
        <div className="metric">
          <div className="k">日报行数</div>
          <div className="v">{rows.length}</div>
        </div>
        <div className="metric">
          <div className="k">平均 F1</div>
          <div className="v accent">{data?.avg_f1?.toFixed(3) ?? '—'}</div>
        </div>
        <div className="metric">
          <div className="k">成功批次</div>
          <div className="v">
            {rows.filter((row) => row.status === 'success').length}
            <small> / {rows.length}</small>
          </div>
        </div>
        <div className="metric">
          <div className="k">CSV 行数</div>
          <div className="v">
            {rows.length + 1}
            <small> 含表头</small>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>价格日报</h2>
          <span className="meta">字段口径：标题 / 标价 / 到手价 / 库存</span>
        </div>
        <div className="panel-body" style={{ padding: 0 }}>
          <table className="data">
            <thead>
              <tr>
                <th>站点</th>
                <th>域名</th>
                <th>快照</th>
                <th>商品标题</th>
                <th>标价</th>
                <th>到手价</th>
                <th>库存</th>
                <th>F1</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.site_id} data-testid={`report-row-${row.site_id}`}>
                  <td>{row.site_name}</td>
                  <td className="mono">{row.domain}</td>
                  <td className="mono">{row.snapshot_label}</td>
                  <td className="wrap">{row.title ?? '—'}</td>
                  <td className="num">{row.list_price ?? '—'}</td>
                  <td className="num">{row.promo_price ?? '—'}</td>
                  <td>{row.stock ?? '—'}</td>
                  <td className="num">{row.f1_score?.toFixed(2) ?? '—'}</td>
                  <td>
                    <StatusPill tone={row.status} label={RUN_STATUS_LABEL[row.status]} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p style={{ marginTop: '0.8rem', fontSize: '0.72rem', color: 'var(--ink-soft)' }}>
        客户只读：模板、快照诊断与告警接口对本角色返回 403；导出动作会写入审计日志。
      </p>
    </div>
  );
}
