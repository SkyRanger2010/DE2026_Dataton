# Подключение Superset к данным

## Trino (Iceberg)

Подключение к витринам в Iceberg через Trino.

**Из контейнера Superset (сеть Docker):**
```
trino://trino:8080/iceberg
```

**С хоста (Superset на localhost или внешний клиент):**
```
trino://localhost:8082/iceberg
```

В Superset: **Settings → Database Connections → + Database** → драйвер **Trino** (или Other), SQLAlchemy URI — одна из строк выше. Пароль по умолчанию не требуется.

## Опциональные настройки Superset

При необходимости можно задать (переменные окружения или конфиг):

| Параметр | Пример | Описание |
|----------|--------|----------|
| ROW_LIMIT | 5000 | Лимит строк по умолчанию в запросах |
| SUPERSET_WORKERS | 4 | Количество воркеров |
| CACHE_CONFIG | `CACHE_TYPE: null` | Отключение кэша при отсутствии Redis |

В основном docker-compose Superset уже использует Redis и общий Postgres для метаданных; дополнительные настройки см. в образе [apache/superset](https://hub.docker.com/r/apache/superset).

## Проверка

В **SQL Lab** выполните:
```sql
SELECT * FROM iceberg.dm.campaign_daily LIMIT 10;
```

Если запрос выполняется, подключение к витрине настроено верно.
