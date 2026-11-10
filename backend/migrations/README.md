# migrations

MySQL 8.0 表结构由 SQLAlchemy 2.0 模型在 backend 启动时 `Base.metadata.create_all()` 创建
（`src/config/app.py::_bootstrap_database`）。`0001_initial.sql` 是与之等价的手工 baseline DDL，
用于审计/离线建库；生产环境请改用 Alembic 生成增量迁移。
