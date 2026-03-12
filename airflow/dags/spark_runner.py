# Общий запуск spark-submit из Airflow (контейнер spark-master через Docker API).
# Не DAG: только хелперы для использования в DAG-файлах.

import shlex


SPARK_MASTER_CONTAINER_PREFIX = "spark-master"
SPARK_SUBMIT = "/opt/spark/bin/spark-submit"
SPARK_MASTER_URL = "spark://spark-master:7077"
PACKAGES_KAFKA = "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3,org.apache.spark:spark-sql-kafka_2.12:3.5.0"
PACKAGES_ICEBERG = "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.4.3"
APP_BASE = "/opt/spark/app/scripts"
IVY_CACHE_DIRS = "/home/spark/.ivy2/cache /home/spark/.ivy2/jars"


def run_spark_script(script_name: str, packages: str) -> None:
    import docker

    client = docker.from_env()
    containers = [c for c in client.containers.list() if SPARK_MASTER_CONTAINER_PREFIX in c.name]
    if not containers:
        raise RuntimeError("Container spark-master not found. Is the stack up?")
    container = containers[0]
    args = [
        SPARK_SUBMIT,
        "--master", SPARK_MASTER_URL,
        "--packages", packages,
        f"{APP_BASE}/{script_name}",
    ]
    cmd_str = " ".join(shlex.quote(a) for a in args)
    full_cmd = f"mkdir -p {IVY_CACHE_DIRS} && {cmd_str}"
    out = container.exec_run(["bash", "-c", full_cmd])
    if out.exit_code != 0:
        raise RuntimeError(f"spark-submit failed: {out.output.decode()}")
    print(out.output.decode())
