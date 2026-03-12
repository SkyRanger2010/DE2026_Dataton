-- Эталонная логика витрины dm.campaign_daily для BI (Superset).
-- По этой спецификации реализованы spark/scripts/ods_to_dm.py (Kafka-поток: impressions, clicks, ctr)
-- и spark/scripts/ods_to_dm_full.py (CSV-поток: полный набор метрик с installs, conversions, revenue).

-- Ежедневное обновление витрины (Postgres: INSERT ... ON CONFLICT DO UPDATE)
INSERT INTO dm.campaign_daily (
    date,
    campaign_id,
    impressions,
    clicks,
    installs,
    conversions,
    revenue,
    ctr,
    cpc,
    cpm,
    conversion_rate,
    processing_date
)
WITH daily_banners AS (
    SELECT 
        DATE(b.event_timestamp) AS date,
        b.campaign_id,
        COUNT(*) AS impressions,
        SUM(b.is_clicked) AS clicks
    FROM ods.fct_banners b
    GROUP BY DATE(b.event_timestamp), b.campaign_id
),
daily_installs AS (
    SELECT 
        DATE(i.install_timestamp) AS date,
        b.campaign_id,
        COUNT(DISTINCT i.user_id) AS installs
    FROM ods.installs i
    JOIN ods.fct_banners b ON i.user_id = b.user_id 
        AND DATE(i.install_timestamp) = DATE(b.event_timestamp)
    GROUP BY DATE(i.install_timestamp), b.campaign_id
),
daily_actions AS (
    SELECT 
        DATE(a.session_start) AS date,
        b.campaign_id,
        COUNT(DISTINCT a.user_id) AS conversions,
        SUM(
            CASE 
                WHEN a.actions = 'first_order' THEN 100
                WHEN a.actions = 'tarrif_switch' THEN 50
                WHEN a.actions = 'registration' THEN 10
                ELSE 0
            END
        ) AS revenue
    FROM ods.fct_actions a
    JOIN ods.fct_banners b ON a.user_id = b.user_id 
        AND DATE(a.session_start) = DATE(b.event_timestamp)
    WHERE a.actions IS NOT NULL AND a.actions != ''
    GROUP BY DATE(a.session_start), b.campaign_id
)
SELECT 
    COALESCE(db.date, di.date, da.date) AS date,
    COALESCE(db.campaign_id, di.campaign_id, da.campaign_id) AS campaign_id,
    COALESCE(db.impressions, 0) AS impressions,
    COALESCE(db.clicks, 0) AS clicks,
    COALESCE(di.installs, 0) AS installs,
    COALESCE(da.conversions, 0) AS conversions,
    COALESCE(da.revenue, 0) AS revenue,
    CASE WHEN COALESCE(db.impressions, 0) > 0 
        THEN ROUND(COALESCE(db.clicks, 0)::DECIMAL / db.impressions * 100, 4) ELSE 0 END AS ctr,
    CASE WHEN COALESCE(db.clicks, 0) > 0 
        THEN ROUND((COALESCE(da.revenue, 0) / db.clicks), 2) ELSE 0 END AS cpc,
    CASE WHEN COALESCE(db.impressions, 0) > 0 
        THEN ROUND((COALESCE(da.revenue, 0) / db.impressions * 1000), 2) ELSE 0 END AS cpm,
    CASE WHEN COALESCE(db.clicks, 0) > 0 
        THEN ROUND(COALESCE(di.installs, 0)::DECIMAL / db.clicks * 100, 4) ELSE 0 END AS conversion_rate,
    CURRENT_DATE AS processing_date
FROM daily_banners db
FULL OUTER JOIN daily_installs di ON db.date = di.date AND db.campaign_id = di.campaign_id
FULL OUTER JOIN daily_actions da ON COALESCE(db.date, di.date) = da.date 
    AND COALESCE(db.campaign_id, di.campaign_id) = da.campaign_id
LEFT JOIN ods.cd_campaign cc ON COALESCE(db.campaign_id, di.campaign_id, da.campaign_id) = cc.campaign_id
ON CONFLICT (date, campaign_id) 
DO UPDATE SET
    impressions = EXCLUDED.impressions,
    clicks = EXCLUDED.clicks,
    installs = EXCLUDED.installs,
    conversions = EXCLUDED.conversions,
    revenue = EXCLUDED.revenue,
    ctr = EXCLUDED.ctr,
    cpc = EXCLUDED.cpc,
    cpm = EXCLUDED.cpm,
    conversion_rate = EXCLUDED.conversion_rate,
    processing_date = EXCLUDED.processing_date;
