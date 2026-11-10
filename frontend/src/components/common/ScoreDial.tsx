interface Props {
  score: number;
  severity: string;
  components: Record<string, number>;
}

const COMPONENT_LABEL: Record<string, string> = {
  path_jaccard: '结构路径 Jaccard',
  node_ratio_delta: '节点数变化率',
  text_similarity: '正文本相似度',
  field_miss_delta: '字段命中率下降',
};

export default function ScoreDial({ score, severity, components }: Props) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  return (
    <div>
      <div className="dial">
        <div>
          <div className="dial-num">{score.toFixed(2)}</div>
          <div className="dial-caption">DOM 漂移评分 · {severity.toUpperCase()}</div>
        </div>
        <div style={{ flex: 1 }}>
          <div className="dial-scale" title="0.35 以上为高危">
            <i style={{ left: `calc(${pct}% - 1px)` }} />
          </div>
          <div className="dial-caption">阈值 0.18 / 0.35；权重 0.4·路径 + 0.2·节点 + 0.2·文本 + 0.2·字段</div>
        </div>
      </div>
      <div style={{ marginTop: '0.9rem' }}>
        {Object.entries(components)
          .filter(([key]) => COMPONENT_LABEL[key])
          .map(([key, value]) => (
            <div className="score" key={key}>
              <span>{COMPONENT_LABEL[key].slice(0, 6)}</span>
              <div className="bar">
                <i style={{ width: `${Math.min(100, Math.max(2, value * 100))}%` }} />
              </div>
              <span className="mono">{value.toFixed(3)}</span>
            </div>
          ))}
      </div>
    </div>
  );
}
