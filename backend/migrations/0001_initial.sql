-- pricelens 初始表结构 baseline（与 src/models 中 SQLAlchemy 模型等价）
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(80) NOT NULL,
  role VARCHAR(20) NOT NULL,
  created_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sites (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL,
  domain VARCHAR(160) NOT NULL UNIQUE,
  market VARCHAR(40) NOT NULL,
  robots_policy VARCHAR(20) NOT NULL,
  qps_limit FLOAT NOT NULL,
  status VARCHAR(20) NOT NULL,
  batch_priority INT NOT NULL,
  note TEXT,
  last_crawled_at DATETIME,
  created_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS extraction_templates (
  id INT PRIMARY KEY AUTO_INCREMENT,
  site_id INT NOT NULL,
  name VARCHAR(120) NOT NULL,
  version INT NOT NULL,
  status VARCHAR(20) NOT NULL,
  field_rules JSON NOT NULL,
  coverage_score FLOAT NOT NULL,
  last_verified_at DATETIME,
  change_note VARCHAR(255),
  created_at DATETIME,
  UNIQUE KEY uq_template_version (site_id, name, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS snapshots (
  id INT PRIMARY KEY AUTO_INCREMENT,
  site_id INT NOT NULL,
  url VARCHAR(400) NOT NULL,
  label VARCHAR(80) NOT NULL,
  captured_at DATETIME NOT NULL,
  html TEXT NOT NULL,
  dom_hash VARCHAR(64) NOT NULL,
  byte_size INT NOT NULL,
  is_baseline TINYINT(1) NOT NULL,
  UNIQUE KEY uq_snapshot_dom (site_id, dom_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS extraction_runs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  template_id INT NOT NULL,
  template_version INT NOT NULL,
  snapshot_id INT NOT NULL,
  status VARCHAR(20) NOT NULL,
  field_results JSON NOT NULL,
  hit_fields INT NOT NULL,
  missing_fields INT NOT NULL,
  f1_score FLOAT,
  duration_ms INT NOT NULL,
  triggered_by VARCHAR(160) NOT NULL,
  seed_key VARCHAR(120) UNIQUE,
  started_at DATETIME,
  finished_at DATETIME,
  error_message VARCHAR(255),
  created_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS drift_alerts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  site_id INT NOT NULL,
  snapshot_id INT NOT NULL,
  template_id INT,
  drift_score FLOAT NOT NULL,
  severity VARCHAR(20) NOT NULL,
  diagnosis JSON NOT NULL,
  suggested_patch JSON NOT NULL,
  status VARCHAR(20) NOT NULL,
  handled_by VARCHAR(160),
  handle_note TEXT,
  created_at DATETIME,
  updated_at DATETIME,
  UNIQUE KEY uq_alert_snapshot (site_id, snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  actor_email VARCHAR(160) NOT NULL,
  actor_role VARCHAR(20) NOT NULL,
  action VARCHAR(60) NOT NULL,
  entity VARCHAR(40) NOT NULL,
  entity_id VARCHAR(40),
  detail JSON NOT NULL,
  ip VARCHAR(60),
  layer VARCHAR(20) NOT NULL,
  seed_key VARCHAR(120) UNIQUE,
  created_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
