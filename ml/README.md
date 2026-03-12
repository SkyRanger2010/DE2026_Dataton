# ML: прогноз клика (CTR) и рекомендация ставок

Задача по архитектуре: прогноз клика (CTR), витрина признаков, XGBoost, batch-инференс. Целевая метрика: **ROC-AUC > 0.8**. Выход: `user_id`, `probability_click`, `segment`, `recommend_bid` (high_spend +20%, low_active стандарт и т.д.).

См. [Архитектура](../docs/ARCHITECTURE.md), [схема ML-слоя](../iceberg/schema_ml.md).

## Схема данных

- **ml.user_features** — витрина признаков (Spark): `user_id`, `snapshot_date`, `impressions_7d`, `clicks_7d`, `actions_7d`, `recency_days`, `device_type`, `os`, `segment`, `tariff`. Партиция по `snapshot_date`.
- **ml.click_predictions** — результат инференса: `user_id`, `snapshot_date`, `probability_click`, `segment`, `recommend_bid`.

## 1. Построение витрины признаков (Spark)

Витрина заполняется из **ods.banner_events** (при наличии — join с ods.fct_actions, ods.cd_user).

```bash
docker compose exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3 \
  /opt/spark/app/scripts/build_ml_user_features.py
```

Опционально: `--snapshot-date 2025-03-01` для фиксированной даты среза.

После выполнения таблица **ml.user_features** в Iceberg готова. Для обучения Python-модели нужно выгрузить данные (например через Trino в CSV/Parquet в `ml/data/user_features.parquet` или сохранить из Spark в `ml/data/`).

## 2. Обучение (XGBoost)

Установка зависимостей: `pip install -r ml/requirements.txt`

```bash
python ml/train.py --features-path ml/data/user_features.parquet --model-path ml/models/xgb_ctr.json
```

- Целевая переменная: бинарная «был ли хотя бы один клик за 7 дней» (`clicks_7d > 0`).
- Признаки: `impressions_7d`, `actions_7d`, `recency_days`, `device_type`, `os`, `segment`, `tariff` (без `clicks_7d`, чтобы не было утечки).
- Модель и метаданные (список признаков, ROC-AUC) сохраняются в `ml/models/`.

## 3. Batch-инференс

```bash
python ml/inference.py \
  --features-path ml/data/user_features.parquet \
  --model-path ml/models/xgb_ctr.json \
  --output-path ml/data/click_predictions.parquet
```

Выход: Parquet с колонками `user_id`, `snapshot_date`, `probability_click`, `segment`, `recommend_bid`. Правила `recommend_bid`: high_spend / высокая вероятность → «+20%», low_active → «стандарт».

## 4. Интеграция с Airflow (опционально)

В DAG можно добавить шаги:

1. Запуск `build_ml_user_features.py` (Spark).
2. Экспорт ml.user_features в `ml/data/` (Spark или Trino) или чтение из MinIO.
3. Запуск `ml/train.py` (если переобучение по расписанию).
4. Запуск `ml/inference.py` и загрузка результата в Iceberg **ml.click_predictions** (Spark или Python + Trino).

## Структура каталога

| Путь | Назначение |
|------|------------|
| `ml/train.py` | Обучение XGBoost по витрине признаков |
| `ml/inference.py` | Batch-инференс, вывод recommend_bid |
| `ml/requirements.txt` | Зависимости Python (pandas, xgboost, scikit-learn, pyarrow) |
| `ml/data/` | Витрина и предсказания (Parquet/CSV) |
| `ml/models/` | Сохранённые модели (xgb_ctr.json, xgb_ctr_meta.json) |
| `spark/scripts/build_ml_user_features.py` | Сбор ml.user_features в Iceberg |

Витрина признаков и предсказания в хранилище описаны в **iceberg/schema_ml.md**.
