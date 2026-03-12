# ODS-слой: сущности по ER-модели

Модель операционного слоя данных (ODS): факты и справочники. Источник: **ER-диаграмма аналитика качества данных** ([Аналитик качества данных/ER сущности.png](../Аналитик%20качества%20данных/ER%20сущности.png)).

---

## Сущности

### Фактовые таблицы

| Таблица | Описание | PK |
|---------|----------|-----|
| **ods.fct_banners** | События показов/кликов по баннерам | — |
| **ods.installs** | События установки приложения | user_id* |
| **ods.fct_actions** | Действия пользователя после установки | — |

\* В реализации один пользователь может иметь несколько установок (источник/время); PK при необходимости — составной или суррогатный.

### Справочники (cd_)

| Таблица | Описание | PK |
|---------|----------|-----|
| **ods.cd_banner** | Описание баннера (креатив, размер, ЦА) | banner_id |
| **ods.cd_campaign** | Кампания (бюджет, даты) | campaign_id |
| **ods.cd_user** | Пользователь (сегмент, тариф) | user_id |

---

## Атрибуты по ER

### ods.fct_banners

| Атрибут | Тип | Описание |
|---------|-----|----------|
| banner_id | long/varchar | ID баннера → **cd_banner.banner_id** |
| campaign_id | long/varchar | ID кампании → **cd_campaign.campaign_id** |
| user_id | long/varchar | ID пользователя → **cd_user.user_id** |
| timestamp / event_timestamp | timestamp | Время события |
| placement | string | Размещение (сайт/приложение/соцсеть) |
| device_type | string | Тип устройства |
| os | string | ОС |
| geo | string | Геолокация |
| is_clicked | int | Признак клика (0/1) |
| processing_date | date | *(служебное)* Дата загрузки |

### ods.cd_banner

| Атрибут | Тип | Описание |
|--------|-----|----------|
| banner_id | long/varchar | **PK** |
| creative_type | string | Тип креатива (статика/видео/анимация) |
| message | string | Текст на баннере |
| size | string | Размер |
| target_audience / target_audience_segment | string | Целевая аудитория |
| processing_date | date | *(служебное)* |

### ods.installs

| Атрибут | Тип | Описание |
|--------|-----|----------|
| user_id | long/varchar | **PK** (или часть PK) → **cd_user.user_id** |
| install_timestamp | timestamp | Время установки |
| source | string | Источник (баннер/органика/другое) |
| processing_date | date | *(служебное)* |

### ods.fct_actions

| Атрибут | Тип | Описание |
|--------|-----|----------|
| user_id | long/varchar | → **cd_user.user_id** |
| session_start | timestamp | Начало сессии |
| action_type / actions | string/text | Тип действия (регистрация, первый заказ и т.д.) |
| processing_date | date | *(служебное)* |

### ods.cd_campaign

| Атрибут | Тип | Описание |
|--------|-----|----------|
| campaign_id | long/varchar | **PK** |
| daily_budget | decimal | Дневной бюджет |
| start_date | date | Начало кампании |
| end_date | date | Окончание кампании |
| impressions, clicks, calculated_cpm, calculated_cpc | *(расчётные)* | Заполняются при ETL (аналитик качества данных) |
| processing_date | date | *(служебное)* |

### ods.cd_user

| Атрибут | Тип | Описание |
|--------|-----|----------|
| user_id | long/varchar | **PK** |
| segment | string | Сегмент |
| tariff | string | Тариф |
| date_create | date | Дата создания |
| date_end | date | Дата окончания (если неактивен) |
| processing_date | date | *(служебное)* |

---

## Связи (ER)

- **fct_banners.banner_id** → **cd_banner.banner_id** (каждый показ ссылается на справочник баннера).
- **fct_banners.campaign_id** → **cd_campaign.campaign_id**.
- **fct_banners.user_id**, **installs.user_id**, **fct_actions.user_id** → **cd_user.user_id** (анализ по пользователю).
- Последовательность событий: показы/клики (**fct_banners**) → установки (**installs**) → действия (**fct_actions**); связь по **user_id** и дате/времени.

---

## Где реализовано

- **Postgres (опционально):** `docker/init/postgres/02-raw-ods-schemas.sql` — все 6 таблиц ODS.
- **Iceberg:** в MVP поток banner_events реализован как **raw.banner_events** → **ods.banner_events** (одна сущность); полный набор ODS-таблиц (fct_banners, installs, fct_actions, cd_*) в Iceberg заполняется скриптами из `sample_data/` — см. `spark/scripts/csv_to_raw_iceberg.py`, `raw_to_ods_iceberg.py` и [data_quality/README.md](../data_quality/README.md).

Иллюстрация модели: **[Аналитик качества данных/ER сущности.png](../Аналитик%20качества%20данных/ER%20сущности.png)**.
