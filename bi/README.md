# BI: дашборды и отчётность

Точка входа по BI в проекте: **Apache Superset**, подключение к витринам через **Trino** (Iceberg).

- **Superset:** http://localhost:8088 (после создания админа: `docker compose exec superset superset fab create-admin` и `superset init`).
- **Подключение к данным:** каталог Trino `iceberg`, схемы `raw`, `ods`, `dm`, `ml`.

Подробная пошаговая инструкция: **[docs/SUPERSET_MVP.md](../docs/SUPERSET_MVP.md)**.

## Содержимое каталога

| Путь | Назначение |
|------|------------|
| **[datasets/](datasets/)** | Спецификации датасетов для Superset (колонки, метрики, источник). |
| **[dashboards/](dashboards/)** | Экспорты дашбордов Superset (YAML); инструкция по импорту. |
| **[superset_connection.md](superset_connection.md)** | Строки подключения к Trino и опциональные настройки Superset. |

## Основной датасет и дашборд MVP

- **Датасет:** `dm.campaign_daily` (схема **dm**, таблица **campaign_daily**). Спецификация: [datasets/dm_campaign_daily.md](datasets/dm_campaign_daily.md).
- **Дашборд:** «Эффективность кампаний» — CTR по кампаниям, показы и клики по дням, таблица по кампаниям/датам. Создаётся вручную по [docs/SUPERSET_MVP.md](../docs/SUPERSET_MVP.md); экспорт можно сохранить в `bi/dashboards/`.

## Источники данных

Витрины в Iceberg заполняются ETL (Spark, Airflow). После запуска пайплайна `banner_events_pipeline` актуальны данные в `dm.campaign_daily`. Эталонная логика метрик витрины: [docs/sql/dm_campaign_daily.sql](../docs/sql/dm_campaign_daily.sql) (аналитик BI).

## Исходные материалы аналитика BI

Каталог **`аналитик bi/`** — отдельный стенд (Postgres + Superset). В основном проекте BI строится по витринам в Iceberg через Trino; логика метрик и список чартов взяты из решений аналитика.
