# Схема данных: banner_events (raw → ods → dm)

Единый контракт для Spark ETL и Superset. Источник событий: топик Kafka `banner_events` или CSV `Fct_banners_show.csv`.

---

## raw.banner_events

Сырой слой: один показ баннера, признак клика в том же событии.

| Поле        | Тип        | Описание |
|-------------|------------|----------|
| event_id    | string     | Уникальный ID события (UUID при загрузке из Kafka; при CSV — генерируется) |
| banner_id   | long       | ID баннера |
| campaign_id | long       | ID кампании |
| user_id     | long       | ID пользователя (допускается NULL до очистки в ODS) |
| event_ts    | timestamp  | Время события |
| event_date  | date       | День события (партиция; для записи в Iceberg) |
| placement   | string     | Размещение: site / app / social |
| device_type | string     | phone / tablet и т.д. |
| os          | string     | ios / android и т.д. |
| geo         | string     | Город/регион |
| is_clicked  | int        | 0 — только показ, 1 — показ и клик |

**Партиционирование:** по полю `event_date`.

---

## ods.banner_events

Нормализованный слой после очистки и дедупликации. Полная модель ODS (все сущности и связи): **[schema_ods_er.md](schema_ods_er.md)** (fct_banners, cd_banner, installs, fct_actions, cd_campaign, cd_user).

- **Поля:** те же, что в raw (включая `event_date`).
- **Правила очистки:**
  - Удаление записей с `user_id IS NULL`.
  - Дедупликация по `(banner_id, user_id, event_ts)` — оставляем одну запись на комбинацию (окно 10 мин по архитектуре; в MVP достаточно `dropDuplicates(banner_id, user_id, event_ts)`).

**Партиционирование:** по полю `event_date`.

---

## dm.campaign_daily

Витрина для BI: агрегаты по кампании и дню. Полная спецификация метрик (в т.ч. installs, conversions, revenue) — **docs/sql/dm_campaign_daily.sql** (логика аналитика BI).

| Поле             | Тип     | Описание |
|------------------|---------|----------|
| campaign_id      | long    | ID кампании |
| date             | date    | День (партиция) |
| impressions      | long    | Число показов |
| clicks           | long    | Число кликов (sum(is_clicked)) |
| installs         | long    | Установки по кампании/дню (из ods.installs) |
| conversions      | long    | Целевые действия (из ods.fct_actions) |
| revenue          | double  | Доход по действиям (first_order=100, tarrif_switch=50, registration=10) |
| ctr              | double  | clicks / impressions * 100 |
| cpc              | double  | revenue / clicks (стоимость за клик) |
| cpm              | double  | revenue / impressions * 1000 |
| conversion_rate  | double  | installs / clicks * 100 |
| processing_date  | date    | Дата обработки |

**MVP:** в `spark/scripts/ods_to_dm.py` реализовано подмножество: impressions, clicks, ctr (без installs/actions). Расширение по эталонному SQL — при появлении ods.installs и ods.fct_actions в Iceberg.

**Партиционирование:** по `date`.

---

## Соответствие CSV (Fct_banners_show)

Колонки CSV: `banner_id;campaign_id;user_id;timestamp;placement (сайт/приложение/соцсеть);device_type;os;geo;is_clicked (0/1)`.

При загрузке из CSV маппинг: `timestamp` → `event_ts`, `placement (сайт/приложение/соцсеть)` → `placement`, `is_clicked (0/1)` → `is_clicked`. Поле `event_id` генерируется (например `uuid` или `banner_id_user_id_timestamp`).

---

Схема слоя ML (витрина признаков, предсказания): **[schema_ml.md](schema_ml.md)**.
