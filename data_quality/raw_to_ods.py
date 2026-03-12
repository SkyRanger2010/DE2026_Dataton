"""
raw (PostgreSQL) -> ods (PostgreSQL).
Читает данные из схемы raw, применяет правила качества (очистка, дедупликация, расчёт CPM/CPC), пишет в ods.
Логика по спецификации аналитика качества данных.
Запуск: при поднятом Postgres и заполненном raw
  python data_quality/raw_to_ods.py
  или через Spark: см. README.
"""
import os
import sys
import logging
from pathlib import Path

# Параметры подключения к PostgreSQL (основной стек DE2026_Dataton)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airflow")
POSTGRES_USER = os.getenv("POSTGRES_USER", "airflow")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airflow")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

POSTGRES_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
POSTGRES_PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver",
}


def create_spark_session():
    from pyspark.sql import SparkSession
    return SparkSession.builder \
        .appName("Raw to ODS (from DB)") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
        .getOrCreate()


def read_from_raw(spark, table):
    return spark.read.jdbc(POSTGRES_URL, f"raw.{table}", properties=POSTGRES_PROPERTIES)


def write_to_ods(spark, df, table, mode="overwrite"):
    df.write.mode(mode).option("truncate", "true").jdbc(
        POSTGRES_URL, f"ods.{table}", properties=POSTGRES_PROPERTIES
    )
    logger.info(f"   ✓ Записано в ods.{table}")


def process_banners(spark):
    """raw.fct_banners_show -> ods.fct_banners (очистка, дедупликация)"""
    logger.info("1. raw.fct_banners_show -> ods.fct_banners...")
    from pyspark.sql.functions import col, row_number
    from pyspark.sql.types import IntegerType, TimestampType
    from pyspark.sql.window import Window

    df = read_from_raw(spark, "fct_banners_show")
    df = df.withColumn("event_timestamp", col("event_timestamp").cast(TimestampType()))
    df = df.withColumn("is_clicked", col("is_clicked").cast(IntegerType()))
    initial = df.count()
    logger.info(f"   Прочитано из raw: {initial} строк")

    df = df.filter(col("user_id").isNotNull())
    logger.info(f"   После удаления NULL user_id: {df.count()} строк")

    w = Window.partitionBy("banner_id", "user_id", "event_timestamp").orderBy("event_timestamp")
    df = df.withColumn("rn", row_number().over(w)).filter(col("rn") == 1).drop("rn")
    logger.info(f"   После дедупликации: {df.count()} строк")

    write_to_ods(spark, df, "fct_banners")
    return df


def process_installs(spark):
    logger.info("2. raw.installs -> ods.installs...")
    from pyspark.sql.types import TimestampType
    from pyspark.sql.functions import col

    df = read_from_raw(spark, "installs")
    df = df.withColumn("install_timestamp", col("install_timestamp").cast(TimestampType()))
    df = df.filter(col("user_id").isNotNull())
    logger.info(f"   Записей: {df.count()}")
    write_to_ods(spark, df, "installs")
    return df


def process_actions(spark):
    logger.info("3. raw.fct_actions -> ods.fct_actions...")
    from pyspark.sql.types import TimestampType
    from pyspark.sql.functions import col

    df = read_from_raw(spark, "fct_actions")
    df = df.withColumn("session_start", col("session_start").cast(TimestampType()))
    df = df.filter(col("user_id").isNotNull())
    logger.info(f"   Записей: {df.count()}")
    write_to_ods(spark, df, "fct_actions")
    return df


def process_banner_meta(spark):
    logger.info("4. raw.cd_banner -> ods.cd_banner...")
    df = read_from_raw(spark, "cd_banner").dropDuplicates(["banner_id"])
    logger.info(f"   Записей: {df.count()}")
    write_to_ods(spark, df, "cd_banner")
    return df


def process_campaign(spark, df_banners):
    """raw.cd_campaign -> ods.cd_campaign с расчётом CPM/CPC по баннерам"""
    logger.info("5. raw.cd_campaign + расчёт CPM/CPC -> ods.cd_campaign...")
    from pyspark.sql.functions import col, when, regexp_replace, to_date
    from pyspark.sql.types import DoubleType

    df = read_from_raw(spark, "cd_campaign")
    df = df.withColumn("daily_budget", regexp_replace(col("daily_budget"), ",", ".").cast(DoubleType()))
    df = df.withColumn("start_date", to_date(col("start_date"), "dd.MM.yyyy"))
    df = df.withColumn("end_date", to_date(col("end_date"), "dd.MM.yyyy"))

    from pyspark.sql.functions import count as spark_count, sum as spark_sum
    banner_stats = df_banners.groupBy("campaign_id").agg(
        spark_count("*").alias("impressions"),
        spark_sum("is_clicked").alias("clicks"),
    )
    banner_stats = banner_stats.withColumn("impressions", col("impressions").cast("long"))
    banner_stats = banner_stats.withColumn("clicks", col("clicks").cast("long"))

    df = df.join(banner_stats, "campaign_id", "left")
    df = df.withColumn("impressions", when(col("impressions").isNull(), 0).otherwise(col("impressions")))
    df = df.withColumn("clicks", when(col("clicks").isNull(), 0).otherwise(col("clicks")))
    df = df.withColumn(
        "calculated_cpm",
        when(col("impressions") > 0, (col("daily_budget") * 1000 / col("impressions")).cast(DoubleType())).otherwise(0.0)
    ).withColumn(
        "calculated_cpc",
        when(col("clicks") > 0, (col("daily_budget") / col("clicks")).cast(DoubleType())).otherwise(0.0)
    )
    df = df.dropDuplicates(["campaign_id"])
    logger.info(f"   Записей: {df.count()}")
    write_to_ods(spark, df, "cd_campaign")
    return df


def process_user(spark):
    logger.info("6. raw.cd_user -> ods.cd_user...")
    from pyspark.sql.types import DateType, TimestampType
    from pyspark.sql.functions import col, to_date

    df = read_from_raw(spark, "cd_user")
    df = df.withColumn("date_create", to_date(col("date_create")))
    df = df.withColumn("date_end", to_date(col("date_end")))
    df = df.filter(col("user_id").isNotNull())
    logger.info(f"   Записей: {df.count()}")
    write_to_ods(spark, df, "cd_user")
    return df


def main():
    logger.info("=" * 60)
    logger.info("Raw (PostgreSQL) -> ODS (PostgreSQL)")
    logger.info("=" * 60)
    spark = None
    try:
        spark = create_spark_session()
        logger.info(f"Подключение: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        df_banners = process_banners(spark)
        process_installs(spark)
        process_actions(spark)
        process_banner_meta(spark)
        process_campaign(spark, df_banners)
        process_user(spark)
        logger.info("=" * 60)
        logger.info("✓ Все данные raw -> ods загружены")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if spark:
            spark.stop()


if __name__ == "__main__":
    main()
