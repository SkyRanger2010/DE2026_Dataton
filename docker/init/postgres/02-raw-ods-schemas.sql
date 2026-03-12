-- ODS в Postgres (опционально, для доступа к нормализованным данным из Postgres).
-- Raw слой хранится в Iceberg (MinIO), не в Postgres. См. spark/scripts/csv_to_raw_iceberg.py, raw_to_ods_iceberg.py.

CREATE SCHEMA IF NOT EXISTS ods;

-- ========== ODS: нормализованный слой (дубликат из Iceberg при необходимости синка) ==========

CREATE TABLE IF NOT EXISTS ods.fct_banners (
    banner_id VARCHAR(50),
    campaign_id VARCHAR(50),
    user_id VARCHAR(50),
    event_timestamp TIMESTAMP,
    placement VARCHAR(100),
    device_type VARCHAR(50),
    os VARCHAR(50),
    geo VARCHAR(50),
    is_clicked INTEGER,
    processing_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS ods.installs (
    user_id VARCHAR(50),
    install_timestamp TIMESTAMP,
    source VARCHAR(100),
    processing_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS ods.fct_actions (
    user_id VARCHAR(50),
    session_start TIMESTAMP,
    actions TEXT,
    processing_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS ods.cd_banner (
    banner_id VARCHAR(50) PRIMARY KEY,
    creative_type VARCHAR(50),
    message TEXT,
    size VARCHAR(50),
    target_audience_segment VARCHAR(100),
    processing_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS ods.cd_campaign (
    campaign_id VARCHAR(50) PRIMARY KEY,
    daily_budget DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    impressions BIGINT,
    clicks BIGINT,
    calculated_cpm DECIMAL(15,2),
    calculated_cpc DECIMAL(15,2),
    processing_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS ods.cd_user (
    user_id VARCHAR(50) PRIMARY KEY,
    segment VARCHAR(50),
    tariff VARCHAR(50),
    date_create DATE,
    date_end DATE,
    processing_date DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_ods_fct_banners_user_id ON ods.fct_banners(user_id);
CREATE INDEX IF NOT EXISTS idx_ods_fct_banners_campaign_id ON ods.fct_banners(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ods_fct_banners_timestamp ON ods.fct_banners(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_ods_installs_user_id ON ods.installs(user_id);
CREATE INDEX IF NOT EXISTS idx_ods_fct_actions_user_id ON ods.fct_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_ods_installs_timestamp ON ods.installs(install_timestamp);
CREATE INDEX IF NOT EXISTS idx_ods_fct_actions_session_start ON ods.fct_actions(session_start);
