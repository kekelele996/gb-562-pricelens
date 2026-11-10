# pricelens · 竞品价格采集与抽取模板自愈台

> 站点改版不可怕，可怕的是第二天才发现日报空了一列。pricelens 用快照漂移诊断 + 候选选择器自愈评分，
> 把「模板静默失效」从第二天提前到当天 06:10。

## 1. 真实场景

- **模拟客户**：「价眼数据」（杭州，12 人），为 6 个 3C/家电品牌提供全网价格日报，覆盖 40 个电商站点。
- **现有工作流**：运营在每站点维护抽取模板（字段 → CSS/XPath 候选选择器 + 后处理正则）；每天 06:00 起采，
  页面 HTML 存快照；抽取商品标题 / 标价 / 促销价 / 券后价 / 库存状态 / 评论数，导出日报。
- **三个痛点**：① 站点改版后模板静默失效（输出 null 或错位值），第二天日报才发现；② 修模板靠人翻 HTML
  试选择器，单站 40–90 分钟；③ 同一字段多套候选选择器（PC/移动/A-B）无管理，覆盖率不明。
- **上下游**：上游=品牌客户 SKU 清单 + 站点清单；本系统替代「模板管理 + 快照诊断 + 候选自愈」；
  下游=BI 日报、缺货预警、客户对账。

## 2. 主要功能

| 页面 | 路径 | 说明 |
|---|---|---|
| 站点与模板总览 | `/sites` | 左侧竖排站点轨道；模板版本 / 覆盖率 / 告警徽章 / 最近抓取 |
| 模板编辑台 | `/templates/:id` | 字段规则（7 字段）、候选选择器编辑、右侧快照抽取预览（命中高亮） |
| 快照诊断 | `/snapshots/:id/diagnose/:templateId` | 漂移评分 + 分项贡献 + 变化子树 top3 + 逐字段命中矩阵 + 候选评分排序 + 一键应用生成 v2 |
| 抽取批次 | `/runs` | 12+ 批次历史、F1 趋势、批次字段矩阵（与诊断页共用 `FieldHitMatrix`） |
| 告警队列 | `/alerts` | 高危/关注/观察队列；候选重算、应用；admin 接受/驳回（审计 +2） |
| 客户日报 | `/client/report` | 品牌客户只读；6 站点价格日报 + CSV 导出（client 访问模板/诊断接口 403） |

## 3. 快速启动

```bash
cp .env.example .env
docker compose up -d --build          # 5 服务：frontend / backend / worker / db / redis
# 等 5/5 healthy（约 60–90s）
open http://localhost:18235
```

seed 会随 backend 启动自动执行一次（`SEED_DEMO=true`），也可手工执行：

```bash
docker compose exec -T backend python -m scripts.seed_demo
# SEED_SUMMARY brand=pricelens sites=6 templates=8 snapshots=12 runs=12 alerts=4 users=3
```

收尾：`docker compose down -v --remove-orphans`。

## 4. 访问地址 / 端口

| 服务 | 容器 | 地址 |
|---|---|---|
| 前端（Nginx + SPA） | `pricelens-frontend` | http://localhost:18235 |
| 后端 API（FastAPI） | `pricelens-backend` | http://localhost:19235/api/health |
| MySQL 8.0 | `pricelens-db` | localhost:17735（库 `pricelens`） |
| Redis 7 | `pricelens-redis` | 容器内 `redis:6379` |
| Celery worker | `pricelens-worker` | 心跳键 `pricelens:worker:heartbeat` |

## 5. 技术栈

| 层 | 选型 |
|---|---|
| 前端 | React 18 + TypeScript + Vite 5 + react-router-dom 6（自研轻量 store + `useSyncExternalStore`） |
| 后端 | Python 3.11 + FastAPI 0.115 + SQLAlchemy 2.0 + PyMySQL + JWT(PyJWT) + passlib(bcrypt) |
| 任务 | Celery 5.4 + Redis（beat 心跳 / 全站巡检 / 异步批次入口） |
| 数据库 | MySQL 8.0（utf8mb4，JSON 字段存字段规则与逐字段结果） |
| 部署 | Docker Compose 5 服务，Nginx `/api/` 反代 + SPA 回落 |

## 6. 目录

```
gb-562/
├── docker-compose.yml         # 5 服务、命名卷、healthcheck、无 version
├── .env / .env.example
├── backend/
│   ├── Dockerfile             # backend 与 worker 共用镜像（worker 覆盖 command）
│   ├── requirements.txt
│   ├── scripts/               # seed_demo.py / build_snapshots.py / demo_config.py
│   ├── migrations/            # 0001_initial.sql baseline DDL + README
│   └── src/
│       ├── config/            # settings / database / celery_app / app
│       ├── constants/         # enums / roles / limits / error_codes / log_templates
│       ├── models/            # 7 张表：users sites templates snapshots runs alerts audit_logs
│       ├── schemas/           # Pydantic 入参出参
│       ├── services/          # 2 个算法 + 领域服务
│       ├── controllers/       # 控制器
│       ├── routes/            # /api 路由
│       ├── middlewares/       # auth / rbac / audit_logger / rate_limit / error_handler
│       └── utils/             # security / textutil / errors / timeutil / logger
└── frontend/
    ├── Dockerfile / nginx.conf
    └── src/{api,stores,types,components,common,hooks,pages,router,utils,constants,styles}
```

## 7. 数据模型（5 核心实体 + 2 支撑）

| 实体 | 关键字段 |
|---|---|
| `Site` | name、domain（唯一）、market、robots_policy、qps_limit、status、last_crawled_at |
| `ExtractionTemplate` | site_id、name、version（(site,name,version) 唯一）、status、field_rules(JSON)、coverage_score、last_verified_at |
| `Snapshot` | site_id、url、captured_at、html(TEXT)、dom_hash（(site,dom_hash) 唯一）、byte_size、is_baseline |
| `ExtractionRun` | template_id、snapshot_id、status、field_results(JSON)、hit/missing_fields、f1_score、duration_ms、seed_key（唯一） |
| `DriftAlert` | site_id、snapshot_id（唯一）、drift_score、severity、diagnosis(JSON)、suggested_patch(JSON)、status、handled_by |
| `User` / `AuditLog` | 3 角色账号；审计含 actor/action/entity/detail/layer（http / domain / seed） |

## 8. 两个核心算法（全部 Python 真算并落库）

### 算法 A：DOM 结构漂移诊断 `src/services/drift_detector.py`

- 输入：baseline 快照 HTML、新快照 HTML、模板 `field_rules`。
- 处理：`html.parser` 构建简化节点（tag / class / 深度 / 文本），路径签名 = 祖先 tag.class 链；
  计算路径集合 Jaccard、节点数比、整页文本 `difflib` 相似度、字段选择器命中率下降 δ。
- 公式：`drift = 0.4·(1-path_jaccard) + 0.2·node_ratio_delta + 0.2·(1-text_sim) + 0.2·field_miss_delta`
- 阈值：`>=0.35 high` / `0.18–0.35 medium` / `<0.18 low`；`<0.09` 不生成告警。
- 输出（落 `DriftAlert.diagnosis`）：`drift_score`、`severity`、`components`、`top_changed_subtrees(3)`、
  `reason_codes[]`、`field_matrix[]`、`affected_fields[]`。
- 失败态：DOM 解析异常 / 空 DOM → `status=unknown` + `reason`，不阻塞队列。
- 可复现：输入快照固定、纯确定性计算、无随机；本项目快照由 `scripts/build_snapshots.py` 生成，sha256 落 `dom_hash`。

### 算法 B：候选选择器自愈评分 `src/services/selector_healer.py`

- 输入：新快照 HTML、模板字段规则（含 `verified_value` 已验证值）、历史批次命中记录。
- 生成 4 类候选：① 旧 selector 的 class 容错变体（同前缀 class / 父级 token 替换）② 同层级兄弟索引
  `:nth-of-type(k)` ③ 文本锚点 XPath（`contains(text(),'到手价')/following-sibling`) ④ tag + 文本模糊匹配。
- 每候选指标：`hit_count`、`value_similarity`（归一化 SequenceMatcher / 数值相对误差 / token Jaccard）、
  `stability`（该站点该字段在历史批次中的正确率，跨模板版本）、`specificity = 1 - min(1, hit_count/total_nodes)`、
  `hit_penalty = min(1, (hit_count-1)/3)`。
- 打分：`score = 0.4·value_similarity + 0.3·stability + 0.2·specificity + 0.1·(1-hit_penalty)`，取 top3；
  `score >= 0.78` 且 `vsim >= 0.6` 才进入自动 patch；全部 miss → `confidence=0, reason=no_candidate`。
- 输出 patch `{field: selector}`；应用后生成模板新版本（version+1，旧版 `deprecated`），并用新版本在同一快照重跑批次。
- 可复现：候选生成顺序固定、无随机；失败态与原因落 `suggested_patch.fields[*].reason`。

## 9. 角色权限（密码统一 `Demo@2026`）

| 角色 | 账号 | 权限 | 典型动作 |
|---|---|---|---|
| 运营主管 | `admin@pricelens.io` | 全部：站点/模板/配额/告警处置/审计 | 接受告警、驳回误报、查看审计 |
| 采集工程师 | `analyst@pricelens.io` | 执行批次、诊断、提交候选、应用候选生成新版本；不能删站点 / 改 QPS | 触发诊断、应用候选、重跑批次 |
| 品牌客户 | `client@pricelens.io` | 只读日报 + 导出 CSV；模板/快照/告警/审计接口一律 403 | 下载日报 CSV |

> 权限差异由后端 `middlewares/rbac.py` + `constants/roles.py` 强制；前端 `constants/roles.ts` 同步控制按钮显隐。

## 10. 共享枚举出现位置

| 枚举组 | 后端 | 前端 |
|---|---|---|
| 角色 Role(admin/analyst/client) | `src/constants/enums.py::Role`、`src/constants/roles.py` | `src/types/models.ts::Role`、`src/constants/roles.ts` |
| 严重级 Severity(high/medium/low/none) | `src/constants/enums.py::Severity`、`drift_detector.py` | `src/types/models.ts::Severity`、`src/constants/enums.ts::SEVERITY_LABEL` |
| 告警状态 AlertStatus(open/accepted/dismissed) | `src/constants/enums.py::AlertStatus` | `src/constants/enums.ts::ALERT_STATUS_LABEL` |
| 模板状态 TemplateStatus(draft/active/deprecated) | `src/constants/enums.py::TemplateStatus` | `src/constants/enums.ts::TEMPLATE_STATUS_LABEL` |
| 批次状态 RunStatus(queued/running/success/failed) | `src/constants/enums.py::RunStatus` | `src/constants/enums.ts::RUN_STATUS_LABEL` |
| 字段状态 FieldStatus(hit/wrong/miss) | `src/constants/enums.py::FieldStatus`、`extraction_service.py` | `src/constants/enums.ts::FIELD_STATUS_LABEL` |
| 候选类型 CandidateKind | `src/constants/enums.py::CandidateKind`、`selector_healer.py` | `src/constants/enums.ts::CANDIDATE_KIND_LABEL` |

## 11. 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `pricelens` | 容器名前缀 / compose 项目名 |
| `FRONTEND_PORT` / `BACKEND_PORT` / `DB_PORT` | 18235 / 19235 / 17735 | 题目分配端口 |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_ROOT_PASSWORD` | pricelens / pricelens / pricelens_pw_2026 / pricelens_root_2026 | MySQL |
| `JWT_SECRET` | pricelens-jwt-secret-change-me-2026 | JWT 签名 |
| `REDIS_URL` | redis://redis:6379/0 | Celery broker/backend + 限流计数 |
| `SEED_DEMO` | true | 启动时跑一次幂等 seed |
| `RATE_LIMIT_PER_MINUTE` / `RATE_LIMIT_RUNS_PER_MINUTE` | 240 / 30 | 全局 / 批次类限流窗口 |

## 12. Docker 说明

- 恰好 5 服务：`frontend`(Nginx) / `backend`(uvicorn) / `worker`(Celery beat+worker) / `db`(MySQL) / `redis`，全部带 healthcheck。
- backend 与 worker 共用同一镜像（`backend/Dockerfile`），worker 通过 compose `command` 覆盖为 Celery。
- 命名卷 `db_data` / `redis_data`；依赖用 `service_healthy`；端口映射全部走 `.env` 变量。
- Nginx：`location /api/ { proxy_pass http://backend:8000/; }` + `try_files ... /index.html` SPA 回落。
- 首次启动约 60–90s（MySQL 初始化 + seed），backend healthcheck `start_period=60s`。

## 13. 本地开发（不走 Docker）

```bash
# 后端
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
DB_HOST=127.0.0.1 DB_PORT=17735 uvicorn src.main:app --reload --port 19235

# 前端：Vite 已配置 /api -> localhost:19235 代理
cd frontend && npm install && npm run dev     # http://localhost:5173
```

## 14. 测试与截图

测试产物与源码分离，全部在 `batch-20261110d/test-artifacts/gb-562/`：

- `tests/smoke.mjs`：健康检查 / 三账号登录 + 403 权限差异 / 诊断 / 候选 / 应用 v2 / 重跑 / CSV / 审计。
- `tests/screenshots.cjs`：用 `_shared/capture.cjs`（零依赖 CDP + 系统 Chrome）截 6 张 1440×900。
- `screenshots/01..06-*.png`、`TESTING.md`（环境、真实数值、已知差异）。

```bash
node test-artifacts/gb-562/tests/smoke.mjs http://localhost:18235
node test-artifacts/gb-562/tests/screenshots.cjs http://localhost:18235
```

## 15. License

MIT（演示项目，数据均为虚构；不真实抓取任何第三方站点）。
