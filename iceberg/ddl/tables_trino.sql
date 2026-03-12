-- DDL Iceberg (Trino): справочные определения таблиц.
-- В MVP таблицы создаются Spark-скриптами (writeTo().createOrReplace()); этот файл — для ручного создания или сверки структуры.
-- Каталог: iceberg, Hive Metastore, warehouse в MinIO.

CREATE SCHEMA IF NOT EXISTS iceberg.raw;
CREATE SCHEMA IF NOT EXISTS iceberg.ods;
CREATE SCHEMA IF NOT EXISTS iceberg.dm;
CREATE SCHEMA IF NOT EXISTS iceberg.ml;

-- raw.banner_events (партиция event_date)
CREATE TABLE IF NOT EXISTS iceberg.raw.banner_events (
    event_id    VARCHAR,
    banner_id   BIGINT,
    campaign_id BIGINT,
    user_id     BIGINT,
    event_ts    TIMESTAMP(6),
    event_date  DATE,
    placement   VARCHAR,
    device_type VARCHAR,
    os          VARCHAR,
    geo         VARCHAR,
    is_clicked  INTEGER
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['event_date']
);

-- ods.banner_events (партиция event_date)
CREATE TABLE IF NOT EXISTS iceberg.ods.banner_events (
    event_id    VARCHAR,
    banner_id   BIGINT,
    campaign_id BIGINT,
    user_id     BIGINT,
    event_ts    TIMESTAMP(6),
    event_date  DATE,
    placement   VARCHAR,
    device_type VARCHAR,
    os          VARCHAR,
    geo         VARCHAR,
    is_clicked  INTEGER
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['event_date']
);

-- dm.campaign_daily (партиция date)
CREATE TABLE IF NOT EXISTS iceberg.dm.campaign_daily (
    campaign_id     BIGINT,
    date            DATE,
    impressions     BIGINT,
    clicks          BIGINT,
    ctr             DOUBLE,
    installs        BIGINT,
    conversions     BIGINT,
    revenue         DOUBLE,
    cpc             DOUBLE,
    cpm             DOUBLE,
    conversion_rate DOUBLE,
    processing_date DATE
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['date']
);

-- ml.user_features (партиция snapshot_date)
CREATE TABLE IF NOT EXISTS iceberg.ml.user_features (
    user_id        BIGINT,
    snapshot_date  DATE,
    impressions_7d BIGINT,
    clicks_7d      BIGINT,
    actions_7d     BIGINT,
    recency_days   INTEGER,
    device_type    VARCHAR,
    os             VARCHAR,
    segment        VARCHAR,
    tariff         VARCHAR
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['snapshot_date']
);

-- ml.click_predictions (партиция snapshot_date)
CREATE TABLE IF NOT EXISTS iceberg.ml.click_predictions (
    user_id           BIGINT,
    snapshot_date     DATE,
    probability_click DOUBLE,
    segment           VARCHAR,
    recommend_bid     VARCHAR
)
WITH (
    format = 'PARQUET',
    partitioning = ARRAY['snapshot_date']
);
