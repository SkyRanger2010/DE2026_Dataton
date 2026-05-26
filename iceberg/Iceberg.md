Хранилище данных для телеком компании. Реализована многоуровневая архитектура (Raw → ODS → DM) на базе Apache Iceberg для консолидации разрозненных данных и поддержки BI/ML задач.

##  Структура файлов:

1. docker-compose_Iceberg.yaml | Docker Compose конфигурация для развертывания инфраструктуры:

- PostgreSQL (5432) - метаданные Iceberg catalog
- Iceberg REST Catalog (8181) - сервис управления таблицами
- MinIO (9000, 9001) - S3-совместимое объектное хранилище
- Spark Iceberg (8888, 8080, 10000, 10001) - движок обработки данных
- MinIO Client (mc) - автоматическое создание бакета warehouse 
2. rqDb.sql | SQL скрипт создания схем и таблиц Iceberg:

- RAW слой (raw_*) - сырые данные из источников
- raw_cd_banner - баннеры
- raw_cd_campaign - кампании
- raw_cd_user - пользователи
- raw_fct_actions - действия пользователей
- raw_installs - установки приложения
- ODS слой (ods_*) - очищенные и нормализованные данные
- ods_dim_banner - справочник баннеров
- ods_dim_campaign - справочник кампаний
- ods_dim_user - справочник пользователей (SCD Type 2)
- ods_fct_actions - факты действий
- ods_fct_installs - факты установок
- DM слой (dm_*) - витрины данных для аналитики
- dm_user_activity_mart - активность пользователей
- dm_campaign_effectiveness_mart - эффективность кампаний
- dm_installs_source_mart - установки по источникам

3. CSV файлы с данными

## Партиционирование:

- Фактовые таблицы: по дате события (days(load_timestamp), event_date)

- Справочники: по ключевым полям (banner_id, campaign_id, is_current)


## Старт

Подключение к Spark Iceberg

> docker exec -it spark-iceberg spark-sql

Выполнение SQL скрипта

> docker exec -i spark-iceberg spark-sql < rqDb.sql

Загрузка данных

>from pyspark.sql import SparkSession

>spark = SparkSession.builder \
    .appName("Load CSV") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .getOrCreate()

Загрузка баннеров
>df = spark.read.option("header", "false").option("delimiter", ";").csv("CD_banner.csv")
df.writeTo("iceberg_db.raw_cd_banner").append()

>USE iceberg_db;
SHOW TABLES;
SELECT * FROM raw_cd_banner LIMIT 10;
SELECT * FROM ods_dim_user WHERE is_current = true LIMIT 10;
SELECT * FROM dm_campaign_effectiveness_mart LIMIT 10;