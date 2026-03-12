# Датасет: dm.campaign_daily

Витрина для дашборда «Эффективность кампаний». Источник: таблица **iceberg.dm.campaign_daily** (Trino).

## Подключение в Superset

- **Database:** Trino (URI `trino://trino:8080/iceberg` или `trino://localhost:8082/iceberg` с хоста).
- **Schema:** dm  
- **Table:** campaign_daily  

Имя датасета в Superset: например **dm.campaign_daily**.

## Колонки

| Колонка | Тип | Описание |
|---------|-----|----------|
| campaign_id | long | ID кампании |
| date | date | День (партиция) |
| impressions | long | Число показов |
| clicks | long | Число кликов |
| ctr | double | Click-through rate (clicks/impressions) |
| installs | long | Установки (при полной витрине) |
| conversions | long | Целевые действия |
| revenue | double | Доход по действиям |
| cpc | double | Стоимость за клик |
| cpm | double | Стоимость за 1000 показов |
| conversion_rate | double | installs/clicks * 100 |
| processing_date | date | Дата обработки |

В MVP в Iceberg обычно заполнены: **campaign_id**, **date**, **impressions**, **clicks**, **ctr**. Остальные колонки добавляются при расширении ETL (ods.installs, ods.fct_actions).

## Рекомендуемые метрики и чарты

- **CTR по кампаниям:** группировка по `campaign_id`, метрика `ctr` (Bar Chart или Table).
- **Показы и клики по дням:** ось X `date`, метрики `impressions`, `clicks` (Line Chart).
- **Таблица:** колонки campaign_id, date, impressions, clicks, ctr (и при наличии — installs, conversions, revenue, cpc, cpm, conversion_rate).

Формулы метрик: [docs/sql/dm_campaign_daily.sql](../../docs/sql/dm_campaign_daily.sql).
