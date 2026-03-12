# Схема слоя ML: витрина признаков и предсказания

Витрины для модели прогноза клика (CTR) и рекомендации ставок. Источник: **ods.banner_events** (и при наличии — ods.fct_actions, ods.cd_user).

---

## ml.user_features

Признаки на уровне пользователя для обучения и инференса (XGBoost, прогноз клика).

| Поле           | Тип     | Описание |
|----------------|---------|----------|
| user_id        | long    | ID пользователя |
| snapshot_date  | date    | Дата среза (партиция) |
| impressions_7d | long    | Показов за последние 7 дней |
| clicks_7d      | long    | Кликов за последние 7 дней |
| actions_7d     | long    | Целевых действий за 7 дней (из ods.fct_actions; 0 если таблицы нет) |
| recency_days   | int     | Дней с последнего показа |
| device_type    | string  | Последний device_type (phone/tablet и т.д.) |
| os             | string  | Последняя ОС (ios/android) |
| segment        | string  | Сегмент из cd_user (или NULL) |
| tariff         | string  | Тариф из cd_user (или NULL) |

**Партиционирование:** по `snapshot_date`. Обновление: ежедневный пересчёт за последние 7 дней (Spark: `spark/scripts/build_ml_user_features.py`).

---

## ml.click_predictions

Выход batch-инференса: вероятность клика и рекомендация ставки по сегменту.

| Поле              | Тип    | Описание |
|-------------------|--------|----------|
| user_id           | long   | ID пользователя |
| snapshot_date      | date   | Дата расчёта |
| probability_click | double | Вероятность клика (0..1) от модели |
| segment           | string | Сегмент (из признаков или cd_user) |
| recommend_bid     | string | Рекомендация ставки: high_spend +20%, low_active стандарт, и т.д. |

**Партиционирование:** по `snapshot_date`. Заполняется скриптом `ml/inference.py` после обучения модели.

---

## Правила recommend_bid (пример)

- **high_spend** (или высокий probability_click): +20% к ставке.
- **low_active** (низкая активность): стандартная ставка.
- Остальные сегменты: по аналогии или по порогам probability_click.

См. [Архитектура](../docs/ARCHITECTURE.md) (раздел ML).
