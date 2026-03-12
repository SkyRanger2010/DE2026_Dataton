"""
Пайплайн событий баннеров: Kafka → raw → ODS → витрина dm.campaign_daily.
Запускает spark-submit в контейнере spark-master через Docker API (нужен сокет и пакет docker).
"""
from datetime import datetime

from airflow.decorators import dag, task

from spark_runner import run_spark_script, PACKAGES_KAFKA, PACKAGES_ICEBERG


@dag(
    dag_id="banner_events_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["mvp", "etl", "banner_events"],
    default_args={"retries": 2},
)
def banner_events_pipeline():
    @task
    def kafka_to_raw():
        run_spark_script("kafka_to_raw.py", PACKAGES_KAFKA)

    @task
    def raw_to_ods():
        run_spark_script("raw_to_ods.py", PACKAGES_ICEBERG)

    @task
    def ods_to_dm():
        run_spark_script("ods_to_dm.py", PACKAGES_ICEBERG)

    kafka_to_raw() >> raw_to_ods() >> ods_to_dm()


banner_events_pipeline()
