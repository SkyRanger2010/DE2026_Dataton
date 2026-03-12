# Заполнение raw / ods / dm / ml через Trino (одноразово для демо)

Данные берутся из CSV в **sample_data**. Скрипт **demo_fill_once.sql** генерируется из этих файлов и затем выполняется в Trino.

**Шаги:**

1. Сгенерировать SQL из CSV (из корня репо):
   ```bash
   python docs/sql/trino/generate_demo_fill_from_csv.py --limit 5000
   ```
   Без `--limit` или с `--limit 0` подтянутся все строки (Fct_banners_show ~1.2M — файл будет очень большим). Для демо достаточно 5000–10000.

2. Выполнить в Trino (каталог `iceberg`) файл **demo_fill_once.sql** целиком или по блокам (1. DDL, 2. RAW, 3. ODS, 4. DM, 5. ML).

Подключение к Trino: с хоста `localhost:8082`, из Docker — хост `trino`, порт 8080. Файл demo_fill_once.sql в репозиторий не включается (см. `.gitignore`).

**Ошибка "Failed connecting to Hive metastore: [hive-metastore:9083]" / "Connection refused"** — Trino не достучится до Hive Metastore. Сделайте по шагам:

1. **Проверить контейнеры:** `docker compose ps` — у **hive-metastore** должен быть статус **Up (healthy)**. Если **Restarting** или **Exit** — метастор падает при старте.
2. **Логи метастора:** `docker compose logs hive-metastore` — при ошибках смотрите JDBC к Postgres (БД hivemeta), доступ к MinIO. Подробнее: docker/README.md.
3. **Перезапуск по порядку:** `docker compose up -d hive-metastore` → подождать 1–2 мин (healthcheck start_period 60 с), затем `docker compose up -d trino`. Либо полный перезапуск: `docker compose restart hive-metastore` и через минуту `docker compose restart trino`.
4. После того как hive-metastore стабильно **Up (healthy)**, перезапустите Trino: `docker compose restart trino`.

---

## Прямая загрузка ML-демо (без CSV)

Скрипт **ml_demo_fill.sql** создаёт схемы/таблицы `iceberg.ml` и вставляет готовые демо-строки в **ml.user_features** и **ml.click_predictions** (20 пользователей, одна дата среза).

**Запуск из корня репо:**

```bash
# Вариант 1: по одному блоку (DDL, затем INSERT user_features, затем INSERT click_predictions)
docker compose exec -i trino trino < docs/sql/trino/ml_demo_fill.sql
```

Если один прогон выполняет только первую команду — откройте `docs/sql/trino/ml_demo_fill.sql` в Trino UI (http://localhost:8082), копируйте и выполняйте блоки по очереди: 1) DDL, 2) INSERT в user_features, 3) INSERT в click_predictions.

---

## Наполнение dm.campaign_daily

Скрипт **dm_campaign_daily_fill.sql** создаёт таблицу `iceberg.dm.campaign_daily` и заполняет её одним из способов:

- **Блок 2 (из ODS)** — расчёт по эталонной логике из `ods.fct_banners`, `ods.installs`, `ods.fct_actions`. Запускать, когда ODS уже заполнен (например, после demo_fill_once или Spark ETL).
- **Блок 3 (демо VALUES)** — готовые строки по 5 кампаниям и нескольким датам (impressions, clicks, ctr, installs, conversions, revenue, cpc, cpm, conversion_rate). Подходит для проверки дашборда в Superset без загрузки ODS.

**Только демо без ODS:** выполните в Trino UI блок 1 (DDL) и блок 3 (INSERT VALUES). Блок 2 пропустите.

**Из корня репо (все блоки):**
```bash
docker compose exec -i trino trino < docs/sql/trino/dm_campaign_daily_fill.sql
```
