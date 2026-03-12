"""
Пайплайн загрузки из CSV (sample_data): raw → ODS → витрина dm.campaign_daily с полными метриками.
Зависимости: справочники и факты уже в raw (через csv_to_raw_iceberg), затем нормализация и расчёт витрины.
"""
from datetime import datetime

from airflow.decorators import dag, task

from spark_runner import run_spark_script, PACKAGES_ICEBERG


@dag(
    dag_id="csv_pipeline",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["etl", "csv", "ods", "dm"],
    default_args={"retries": 2},
)
def csv_pipeline():
    @task
    def csv_to_raw():
        run_spark_script("csv_to_raw_iceberg.py", PACKAGES_ICEBERG)

    @task
    def raw_to_ods():
        run_spark_script("raw_to_ods_iceberg.py", PACKAGES_ICEBERG)

    @task
    def ods_to_dm_full():
        run_spark_script("ods_to_dm_full.py", PACKAGES_ICEBERG)

    csv_to_raw() >> raw_to_ods() >> ods_to_dm_full()


csv_pipeline()
