-- Создание bd
CREATE DATABASE IF NOT EXISTS iceberg_db;
USE iceberg_db;


-- 1. RAW Слой
-- Баннеры
CREATE TABLE iceberg_db.raw_cd_banner (
    banner_id STRING,
    creative_type STRING,
    message STRING,
    size STRING,
    target_audience_segment STRING,
    load_timestamp TIMESTAMP,
    source_file STRING
) USING iceberg
PARTITIONED BY (days(load_timestamp))
LOCATION '/warehouse/iceberg_db/raw_cd_banner';

-- Кампании
CREATE TABLE iceberg_db.raw_cd_campaign (
    campaign_id STRING,
    daily_budget STRING,
    start_date STRING,
    end_date STRING,
    load_timestamp TIMESTAMP,
    source_file STRING
) USING iceberg
PARTITIONED BY (days(load_timestamp))
LOCATION '/warehouse/iceberg_db/raw_cd_campaign';

-- Пользователи
CREATE TABLE iceberg_db.raw_cd_user (
    user_id STRING,
    segment STRING,
    tariff STRING,
    date_create STRING,
    date_end STRING,
    load_timestamp TIMESTAMP,
    source_file STRING
) USING iceberg
PARTITIONED BY (days(load_timestamp))
LOCATION '/warehouse/iceberg_db/raw_cd_user';

-- Действия пользователей
CREATE TABLE iceberg_db.raw_fct_actions (
    user_id STRING,
    session_start STRING,
    actions STRING,
    load_timestamp TIMESTAMP,
    source_file STRING
) USING iceberg
PARTITIONED BY (days(load_timestamp))
LOCATION '/warehouse/iceberg_db/raw_fct_actions';

-- Установки приложения
CREATE TABLE iceberg_db.raw_installs (
    user_id STRING,
    install_timestamp STRING,
    source STRING,
    load_timestamp TIMESTAMP,
    source_file STRING
) USING iceberg
PARTITIONED BY (days(load_timestamp))
LOCATION '/warehouse/iceberg_db/raw_installs';


-- 2. ODS Слой
-- Справочник баннеров
CREATE TABLE iceberg_db.ods_dim_banner (
    banner_id INT,
    creative_type STRING,
    message STRING,
    size STRING,
    target_audience_segment STRING,
    updated_at TIMESTAMP
) USING iceberg
PARTITIONED BY (banner_id)
LOCATION '/warehouse/iceberg_db/ods_dim_banner';

-- Справочник кампаний
CREATE TABLE iceberg_db.ods_dim_campaign (
    campaign_id INT,
    daily_budget DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    cpm DECIMAL(10,2),
    cpc DECIMAL(10,2),
    updated_at TIMESTAMP
) USING iceberg
PARTITIONED BY (campaign_id)
LOCATION '/warehouse/iceberg_db/ods_dim_campaign';

-- Справочник пользователей (SCD Type 2)
CREATE TABLE iceberg_db.ods_dim_user (
    user_id INT,
    segment STRING,
    tariff STRING,
    date_create DATE,
    date_end DATE,
    is_current BOOLEAN,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP
) USING iceberg
PARTITIONED BY (is_current)
LOCATION '/warehouse/iceberg_db/ods_dim_user';

-- Факт действий
CREATE TABLE iceberg_db.ods_fct_actions (
    user_id INT,
    session_start TIMESTAMP,
    action_type STRING,
    event_date DATE
) USING iceberg
PARTITIONED BY (event_date)
LOCATION '/warehouse/iceberg_db/ods_fct_actions';

-- Факт установок
CREATE TABLE iceberg_db.ods_fct_installs (
    user_id INT,
    install_timestamp TIMESTAMP,
    source STRING,
    install_date DATE
) USING iceberg
PARTITIONED BY (install_date)
LOCATION '/warehouse/iceberg_db/ods_fct_installs';


-- 3. DM Слой
-- Витрина активности пользователей
CREATE TABLE iceberg_db.dm_user_activity_mart (
    user_id INT,
    segment STRING,
    tariff STRING,
    registration_date DATE,
    first_order_date DATE,
    last_action_date DATE,
    total_actions INT,
    orders_count INT,
    tariff_switches_count INT,
    days_since_last_action INT,
    is_active BOOLEAN,
    snapshot_date DATE
) USING iceberg
PARTITIONED BY (snapshot_date)
LOCATION '/warehouse/iceberg_db/dm_user_activity_mart';

-- Витрина эффективности кампаний
CREATE TABLE iceberg_db.dm_campaign_effectiveness_mart (
    campaign_id INT,
    banner_id INT,
    target_audience_segment STRING,
    impressions_count BIGINT,
    clicks_count BIGINT,
    installs_count BIGINT,
    registrations_count BIGINT,
    orders_count BIGINT,
    daily_budget DECIMAL(15,2),
    ctr DECIMAL(5,4),
    conversion_rate DECIMAL(5,4),
    cpa DECIMAL(10,2),
    report_date DATE
) USING iceberg
PARTITIONED BY (report_date)
LOCATION '/warehouse/iceberg_db/dm_campaign_effectiveness_mart';

-- Витрина установок по источникам
CREATE TABLE iceberg_db.dm_installs_source_mart (
    source STRING,
    install_date DATE,
    installs_count BIGINT,
    registrations_count BIGINT,
    conversion_rate DECIMAL(5,4),
    week_number INT
) USING iceberg
PARTITIONED BY (install_date)
LOCATION '/warehouse/iceberg_db/dm_installs_source_mart';


-- 3. Проверка:
-- Просмотр таблиц
SHOW TABLES IN iceberg_db;

-- Проверка данных
SELECT * FROM iceberg_db.raw_cd_banner LIMIT 10;
SELECT * FROM iceberg_db.ods_dim_user WHERE is_current = true LIMIT 10;
SELECT * FROM iceberg_db.dm_campaign_effectiveness_mart LIMIT 10;

-- Проверка истории
SELECT * FROM iceberg_db.raw_cd_banner 
TIMESTAMP AS OF '2025-03-11 00:00:00';

-- Проверка снапшотов
SELECT * FROM iceberg_db.raw_cd_banner.history;