#!/usr/bin/env python3
"""
Генерация demo_fill_once.sql из CSV в sample_data.
Читает все CSV, формирует INSERT VALUES и дописывает блоки ODS/DM/ML.
Запуск из корня репо: python docs/sql/trino/generate_demo_fill_from_csv.py [--limit 5000]
"""
import argparse
import csv
from pathlib import Path


def norm(row: dict) -> dict:
    return {k.strip().lstrip("\ufeff"): v for k, v in row.items()}


def esc(s: str) -> str:
    if s is None or (isinstance(s, str) and s.strip().upper() in ("", "NULL")):
        return "NULL"
    return "'" + str(s).replace("\\", "\\\\").replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10000, help="Макс. строк для Fct_banners_show и CD_user (0 = все)")
    ap.add_argument("--sample-data", type=str, default=None, help="Путь к sample_data")
    args = ap.parse_args()
    script_dir = Path(__file__).resolve().parent
    base = Path(args.sample_data) if args.sample_data else script_dir / ".." / ".." / ".." / "sample_data"
    base = base.resolve()
    out_file = script_dir / "demo_fill_once.sql"
    if not base.exists():
        print(f"Каталог не найден: {base}")
        return

    lines = [
        "-- Сгенерировано из sample_data (generate_demo_fill_from_csv.py). Выполнить в Trino (каталог iceberg).",
        "",
        "-- ========== 1. DDL ==========",
        "CREATE SCHEMA IF NOT EXISTS iceberg.raw;",
        "CREATE SCHEMA IF NOT EXISTS iceberg.ods;",
        "CREATE SCHEMA IF NOT EXISTS iceberg.dm;",
        "CREATE SCHEMA IF NOT EXISTS iceberg.ml;",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.raw.fct_banners_show (",
        "    banner_id BIGINT, campaign_id BIGINT, user_id BIGINT, event_timestamp TIMESTAMP(6),",
        "    placement VARCHAR, device_type VARCHAR, os VARCHAR, geo VARCHAR, is_clicked INTEGER",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.raw.installs (",
        "    user_id BIGINT, install_timestamp TIMESTAMP(6), source VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.raw.fct_actions (",
        "    user_id BIGINT, session_start TIMESTAMP(6), actions VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.raw.cd_banner (",
        "    banner_id BIGINT, creative_type VARCHAR, message VARCHAR, size VARCHAR, target_audience_segment VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.raw.cd_campaign (",
        "    campaign_id BIGINT, daily_budget VARCHAR, start_date VARCHAR, end_date VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.raw.cd_user (",
        "    user_id BIGINT, segment VARCHAR, tariff VARCHAR, date_create VARCHAR, date_end VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ods.fct_banners (",
        "    banner_id BIGINT, campaign_id BIGINT, user_id BIGINT, event_timestamp TIMESTAMP(6),",
        "    placement VARCHAR, device_type VARCHAR, os VARCHAR, geo VARCHAR, is_clicked INTEGER",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ods.installs (",
        "    user_id BIGINT, install_timestamp TIMESTAMP(6), source VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ods.fct_actions (",
        "    user_id BIGINT, session_start TIMESTAMP(6), actions VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ods.cd_banner (",
        "    banner_id BIGINT, creative_type VARCHAR, message VARCHAR, size VARCHAR, target_audience_segment VARCHAR",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ods.cd_campaign (",
        "    campaign_id BIGINT, daily_budget DOUBLE, start_date DATE, end_date DATE,",
        "    impressions BIGINT, clicks BIGINT, calculated_cpm DOUBLE, calculated_cpc DOUBLE",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ods.cd_user (",
        "    user_id BIGINT, segment VARCHAR, tariff VARCHAR, date_create DATE, date_end DATE",
        ") WITH (format = 'PARQUET');",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.dm.campaign_daily (",
        "    campaign_id BIGINT, date DATE, impressions BIGINT, clicks BIGINT, ctr DOUBLE,",
        "    installs BIGINT, conversions BIGINT, revenue DOUBLE, cpc DOUBLE, cpm DOUBLE,",
        "    conversion_rate DOUBLE, processing_date DATE",
        ") WITH (format = 'PARQUET', partitioning = ARRAY['date']);",
        "",
        "CREATE TABLE IF NOT EXISTS iceberg.ml.user_features (",
        "    user_id BIGINT, snapshot_date DATE, impressions_7d BIGINT, clicks_7d BIGINT, actions_7d BIGINT,",
        "    recency_days INTEGER, device_type VARCHAR, os VARCHAR, segment VARCHAR, tariff VARCHAR",
        ") WITH (format = 'PARQUET', partitioning = ARRAY['snapshot_date']);",
        "",
        "-- ========== 2. RAW (данные из CSV sample_data) ==========",
    ]

    # Fct_banners_show
    path = base / "Fct_banners_show.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = [norm(r) for r in csv.DictReader(f, delimiter=";")]
        if args.limit:
            rows = rows[: args.limit]
        vals = []
        for r in rows:
            ts = (r.get("timestamp") or "").strip()
            ts_sql = f"TIMESTAMP '{ts}'" if ts else "NULL"
            pl = r.get("placement (сайт/приложение/соцсеть)") or r.get("placement")
            cl = r.get("is_clicked (0/1)") or r.get("is_clicked") or 0
            vals.append(f"({r.get('banner_id')},{r.get('campaign_id')},{r.get('user_id')},{ts_sql},{esc(pl)},{esc(r.get('device_type'))},{esc(r.get('os'))},{esc(r.get('geo'))},{cl})")
        lines.append("INSERT INTO iceberg.raw.fct_banners_show (banner_id, campaign_id, user_id, event_timestamp, placement, device_type, os, geo, is_clicked) VALUES")
        lines.append(",\n".join(vals) + ";")
        lines.append("")
        print(f"fct_banners_show: {len(rows)} строк")

    # Installs
    path = base / "Installs.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = [norm(r) for r in csv.DictReader(f, delimiter=";")]
        vals = []
        for r in rows:
            ts = (r.get("install_timestamp") or "").strip()
            ts_sql = f"TIMESTAMP '{ts}'" if ts else "NULL"
            src = r.get("source (баннер / органика / другое)") or r.get("source")
            vals.append(f"({r.get('user_id')},{ts_sql},{esc(src)})")
        lines.append("INSERT INTO iceberg.raw.installs (user_id, install_timestamp, source) VALUES")
        lines.append(",\n".join(vals) + ";")
        lines.append("")
        print(f"installs: {len(rows)} строк")

    # Fct_actions
    path = base / "Fct_actions.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = [norm(r) for r in csv.DictReader(f, delimiter=";")]
        vals = []
        for r in rows:
            ts = (r.get("session_start") or "").strip()
            ts_sql = f"TIMESTAMP '{ts}'" if ts else "NULL"
            ac = r.get("actions (регистрация, первый заказ и т.д.)") or r.get("actions")
            vals.append(f"({r.get('user_id')},{ts_sql},{esc(ac)})")
        lines.append("INSERT INTO iceberg.raw.fct_actions (user_id, session_start, actions) VALUES")
        lines.append(",\n".join(vals) + ";")
        lines.append("")
        print(f"fct_actions: {len(rows)} строк")

    # CD_banner
    path = base / "CD_banner.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = [norm(r) for r in csv.DictReader(f, delimiter=";")]
        ct = "creative_type (статика/видео/анимация)"
        msg = "message (сообщение на баннере)"
        vals = []
        for r in rows:
            vals.append(f"({r.get('banner_id')},{esc(r.get(ct, r.get('creative_type')))},{esc(r.get(msg, r.get('message')))},{esc(r.get('size'))},{esc(r.get('target_audience_segment'))})")
        lines.append("INSERT INTO iceberg.raw.cd_banner (banner_id, creative_type, message, size, target_audience_segment) VALUES")
        lines.append(",\n".join(vals) + ";")
        lines.append("")
        print(f"cd_banner: {len(rows)} строк")

    # CD_campaign
    path = base / "CD_campaign.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = [norm(r) for r in csv.DictReader(f, delimiter=";")]
        vals = []
        for r in rows:
            vals.append(f"({r.get('campaign_id')},{esc(r.get('daily_budget'))},{esc(r.get('start_date'))},{esc(r.get('end_date'))})")
        lines.append("INSERT INTO iceberg.raw.cd_campaign (campaign_id, daily_budget, start_date, end_date) VALUES")
        lines.append(",\n".join(vals) + ";")
        lines.append("")
        print(f"cd_campaign: {len(rows)} строк")

    # CD_user
    path = base / "CD_user.csv"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = [norm(r) for r in csv.DictReader(f, delimiter=";")]
        if args.limit:
            rows = rows[: args.limit]
        vals = []
        for r in rows:
            uid = r.get("User_id") or r.get("user_id")
            dc = (r.get("date_create") or "").strip()
            de = (r.get("date_end") or "").strip()
            dc_sql = f"DATE '{dc}'" if dc else "NULL"
            de_sql = f"DATE '{de}'" if de else "NULL"
            vals.append(f"({uid},{esc(r.get('segment'))},{esc(r.get('tariff'))},{dc_sql},{de_sql})")
        lines.append("INSERT INTO iceberg.raw.cd_user (user_id, segment, tariff, date_create, date_end) VALUES")
        lines.append(",\n".join(vals) + ";")
        lines.append("")
        print(f"cd_user: {len(rows)} строк")

    # 3–5: ODS, DM, ML (фиксированный блок)
    lines.extend([
        "-- ========== 3. ODS из raw ==========",
        "INSERT INTO iceberg.ods.fct_banners",
        "SELECT banner_id, campaign_id, user_id, event_timestamp, placement, device_type, os, geo, is_clicked",
        "FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY banner_id, user_id, event_timestamp ORDER BY event_timestamp) AS rn",
        "      FROM iceberg.raw.fct_banners_show WHERE user_id IS NOT NULL) t WHERE rn = 1;",
        "",
        "INSERT INTO iceberg.ods.installs SELECT user_id, install_timestamp, source FROM iceberg.raw.installs WHERE user_id IS NOT NULL;",
        "",
        "INSERT INTO iceberg.ods.fct_actions SELECT user_id, session_start, actions FROM iceberg.raw.fct_actions WHERE user_id IS NOT NULL;",
        "",
        "INSERT INTO iceberg.ods.cd_banner",
        "SELECT banner_id, creative_type, message, size, target_audience_segment",
        "FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY banner_id ORDER BY banner_id) AS rn FROM iceberg.raw.cd_banner) t WHERE rn = 1;",
        "",
        "INSERT INTO iceberg.ods.cd_campaign",
        "SELECT c.campaign_id, CAST(REPLACE(TRIM(c.daily_budget), ',', '.') AS DOUBLE),",
        "  date(date_parse(TRIM(c.start_date), '%d.%m.%Y')), date(date_parse(TRIM(c.end_date), '%d.%m.%Y')),",
        "  COALESCE(s.impressions, 0), COALESCE(s.clicks, 0),",
        "  CASE WHEN COALESCE(s.impressions, 0) > 0 THEN CAST(REPLACE(TRIM(c.daily_budget), ',', '.') AS DOUBLE) * 1000.0 / s.impressions ELSE 0 END,",
        "  CASE WHEN COALESCE(s.clicks, 0) > 0 THEN CAST(REPLACE(TRIM(c.daily_budget), ',', '.') AS DOUBLE) / s.clicks ELSE 0 END",
        "FROM iceberg.raw.cd_campaign c",
        "LEFT JOIN (SELECT campaign_id, COUNT(*) AS impressions, SUM(is_clicked) AS clicks FROM iceberg.ods.fct_banners GROUP BY campaign_id) s ON c.campaign_id = s.campaign_id;",
        "",
        "INSERT INTO iceberg.ods.cd_user",
        "SELECT user_id, segment, tariff,",
        "  CASE WHEN TRIM(date_create) != '' THEN CAST(TRIM(date_create) AS DATE) ELSE NULL END,",
        "  CASE WHEN TRIM(COALESCE(date_end, '')) != '' THEN CAST(TRIM(date_end) AS DATE) ELSE NULL END",
        "FROM iceberg.raw.cd_user WHERE user_id IS NOT NULL;",
        "",
        "-- ========== 4. DM из ODS ==========",
        "INSERT INTO iceberg.dm.campaign_daily (campaign_id, date, impressions, clicks, ctr, installs, conversions, revenue, cpc, cpm, conversion_rate, processing_date)",
        "WITH db AS (SELECT CAST(event_timestamp AS DATE) AS date, campaign_id, COUNT(*) AS impressions, SUM(is_clicked) AS clicks FROM iceberg.ods.fct_banners GROUP BY 1, 2),",
        "     di AS (SELECT CAST(i.install_timestamp AS DATE) AS date, b.campaign_id, COUNT(DISTINCT i.user_id) AS installs",
        "            FROM iceberg.ods.installs i JOIN iceberg.ods.fct_banners b ON i.user_id = b.user_id AND CAST(i.install_timestamp AS DATE) = CAST(b.event_timestamp AS DATE) GROUP BY 1, 2),",
        "     da AS (SELECT CAST(a.session_start AS DATE) AS date, b.campaign_id, COUNT(DISTINCT a.user_id) AS conversions,",
        "            SUM(CASE WHEN a.actions = 'first_order' THEN 100 WHEN a.actions = 'tarrif_switch' THEN 50 WHEN a.actions = 'registration' THEN 10 ELSE 0 END) AS revenue",
        "            FROM iceberg.ods.fct_actions a JOIN iceberg.ods.fct_banners b ON a.user_id = b.user_id AND CAST(a.session_start AS DATE) = CAST(b.event_timestamp AS DATE)",
        "            WHERE a.actions IS NOT NULL AND TRIM(a.actions) != '' GROUP BY 1, 2),",
        "     c AS (SELECT COALESCE(db.date, di.date, da.date) AS date, COALESCE(db.campaign_id, di.campaign_id, da.campaign_id) AS campaign_id,",
        "            COALESCE(db.impressions, 0) AS impressions, COALESCE(db.clicks, 0) AS clicks, COALESCE(di.installs, 0) AS installs,",
        "            COALESCE(da.conversions, 0) AS conversions, COALESCE(da.revenue, 0.0) AS revenue",
        "            FROM db FULL OUTER JOIN di ON db.date = di.date AND db.campaign_id = di.campaign_id",
        "            FULL OUTER JOIN da ON COALESCE(db.date, di.date) = da.date AND COALESCE(db.campaign_id, di.campaign_id) = da.campaign_id)",
        "SELECT campaign_id, date, impressions, clicks,",
        "  CASE WHEN impressions > 0 THEN ROUND(clicks * 100.0 / impressions, 4) ELSE 0 END,",
        "  installs, conversions, revenue,",
        "  CASE WHEN clicks > 0 THEN ROUND(revenue / clicks, 2) ELSE 0 END,",
        "  CASE WHEN impressions > 0 THEN ROUND(revenue * 1000.0 / impressions, 2) ELSE 0 END,",
        "  CASE WHEN clicks > 0 THEN ROUND(installs * 100.0 / clicks, 4) ELSE 0 END,",
        "  CURRENT_DATE FROM c WHERE date IS NOT NULL AND campaign_id IS NOT NULL;",
        "",
        "-- ========== 5. ML из ODS ==========",
        "INSERT INTO iceberg.ml.user_features (user_id, snapshot_date, impressions_7d, clicks_7d, actions_7d, recency_days, device_type, os, segment, tariff)",
        "WITH s AS (SELECT CURRENT_DATE AS snapshot_date),",
        "     w AS (SELECT b.user_id, b.event_timestamp, b.is_clicked, b.device_type, b.os",
        "           FROM iceberg.ods.fct_banners b CROSS JOIN s",
        "           WHERE CAST(b.event_timestamp AS DATE) >= s.snapshot_date - INTERVAL '7' DAY AND CAST(b.event_timestamp AS DATE) < s.snapshot_date),",
        "     u AS (SELECT user_id, COUNT(*) AS impressions_7d, SUM(is_clicked) AS clicks_7d, MAX(event_timestamp) AS last_ts, MAX(device_type) AS device_type, MAX(os) AS os FROM w GROUP BY user_id),",
        "     a AS (SELECT a.user_id, COUNT(*) AS actions_7d FROM iceberg.ods.fct_actions a CROSS JOIN s",
        "           WHERE CAST(a.session_start AS DATE) >= s.snapshot_date - INTERVAL '7' DAY AND CAST(a.session_start AS DATE) < s.snapshot_date GROUP BY a.user_id)",
        "SELECT u.user_id, (SELECT snapshot_date FROM s), u.impressions_7d, u.clicks_7d, COALESCE(a.actions_7d, 0),",
        "  date_diff('day', CAST(u.last_ts AS DATE), (SELECT snapshot_date FROM s)), u.device_type, u.os, c.segment, c.tariff",
        "FROM u LEFT JOIN a ON u.user_id = a.user_id LEFT JOIN iceberg.ods.cd_user c ON u.user_id = c.user_id;",
    ])

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Записано: {out_file}")
    print("Выполните в Trino: demo_fill_once.sql")


if __name__ == "__main__":
    main()
