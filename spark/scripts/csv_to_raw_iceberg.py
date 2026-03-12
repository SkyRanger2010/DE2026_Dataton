"""
Загрузка CSV из sample_data в raw-слой Iceberg (fct_banners_show, installs, fct_actions, справочники).
Разделитель — точка с запятой, пути задаются через CSV_BASE_PATH. Нужен для демо и проверки качества данных.
"""
import os
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import IntegerType

CSV_BASE = os.environ.get("CSV_BASE_PATH", "/opt/spark/app/sample_data")


def main():
    spark = SparkSession.builder.getOrCreate()
    base = Path(CSV_BASE)
    if not base.exists():
        print(f"Каталог не найден: {base}. Задайте CSV_BASE_PATH.")
        return

    spark.sql("CREATE DATABASE IF NOT EXISTS raw")

    # Fct_banners_show
    path = base / "Fct_banners_show.csv"
    if path.exists():
        df = spark.read.option("header", "true").option("delimiter", ";").option("quote", '"').csv(str(path))
        for old in df.columns:
            new = "".join(c if c.isalnum() or c == "_" else "_" for c in old).replace("__", "_").strip("_") or "col"
            if new != old:
                df = df.withColumnRenamed(old, new)
        df = df.withColumnRenamed("timestamp", "event_timestamp") \
            .withColumnRenamed("placement_сайт_приложение_соцсеть", "placement") \
            .withColumnRenamed("is_clicked_0_1", "is_clicked")
        df = df.withColumn("event_timestamp", to_timestamp(col("event_timestamp")))
        df = df.withColumn("is_clicked", col("is_clicked").cast(IntegerType()))
        df.writeTo("spark_catalog.raw.fct_banners_show").using("iceberg").tableProperty("format-version", "2").createOrReplace()
        print("raw.fct_banners_show OK")

    # Installs
    path = base / "Installs.csv"
    if path.exists():
        df = spark.read.option("header", "true").option("delimiter", ";").csv(str(path))
        for old in df.columns:
            new = "".join(c if c.isalnum() or c == "_" else "_" for c in old).replace("__", "_").strip("_") or "col"
            if new != old:
                df = df.withColumnRenamed(old, new)
        df = df.withColumnRenamed("source_баннер_органика_другое", "source") \
            .withColumn("install_timestamp", to_timestamp(col("install_timestamp")))
        df.writeTo("spark_catalog.raw.installs").using("iceberg").tableProperty("format-version", "2").createOrReplace()
        print("raw.installs OK")

    # Fct_actions
    path = base / "Fct_actions.csv"
    if path.exists():
        df = spark.read.option("header", "true").option("delimiter", ";").csv(str(path))
        for old in df.columns:
            new = "".join(c if c.isalnum() or c == "_" else "_" for c in old).replace("__", "_").strip("_") or "col"
            if new != old:
                df = df.withColumnRenamed(old, new)
        df = df.withColumnRenamed("actions_регистрация_первый_заказ_и_т_д", "actions") \
            .withColumn("session_start", to_timestamp(col("session_start")))
        df.writeTo("spark_catalog.raw.fct_actions").using("iceberg").tableProperty("format-version", "2").createOrReplace()
        print("raw.fct_actions OK")

    # CD_banner
    path = base / "CD_banner.csv"
    if path.exists():
        df = spark.read.option("header", "true").option("delimiter", ";").csv(str(path))
        for old in df.columns:
            new = "".join(c if c.isalnum() or c == "_" else "_" for c in old).replace("__", "_").strip("_") or "col"
            if new != old:
                df = df.withColumnRenamed(old, new)
        df = df.withColumnRenamed("creative_type_статика_видео_анимация", "creative_type") \
            .withColumnRenamed("message_сообщение_на_баннере", "message")
        df.writeTo("spark_catalog.raw.cd_banner").using("iceberg").tableProperty("format-version", "2").createOrReplace()
        print("raw.cd_banner OK")

    # CD_campaign
    path = base / "CD_campaign.csv"
    if path.exists():
        df = spark.read.option("header", "true").option("delimiter", ";").csv(str(path))
        for old in df.columns:
            new = "".join(c if c.isalnum() or c == "_" else "_" for c in old).replace("__", "_").strip("_") or "col"
            if new != old:
                df = df.withColumnRenamed(old, new)
        df.writeTo("spark_catalog.raw.cd_campaign").using("iceberg").tableProperty("format-version", "2").createOrReplace()
        print("raw.cd_campaign OK")

    # CD_user
    path = base / "CD_user.csv"
    if path.exists():
        df = spark.read.option("header", "true").option("delimiter", ";").csv(str(path))
        for old in df.columns:
            new = "".join(c if c.isalnum() or c == "_" else "_" for c in old).replace("__", "_").strip("_") or "col"
            if new != old:
                df = df.withColumnRenamed(old, new)
        df = df.withColumnRenamed("User_id", "user_id")
        df.writeTo("spark_catalog.raw.cd_user").using("iceberg").tableProperty("format-version", "2").createOrReplace()
        print("raw.cd_user OK")

    print("Готово: raw (Iceberg) заполнен из CSV.")


if __name__ == "__main__":
    main()
