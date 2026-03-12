# Создание топиков Kafka для DE2026_Dataton.
# Запуск из корня репо после docker compose up: .\kafka\create_topic.ps1

$Partitions = if ($env:PARTITIONS) { $env:PARTITIONS } else { 6 }
$Replication = if ($env:REPLICATION) { $env:REPLICATION } else { 1 }

$topics = @(
    "banner_events",   # Spark kafka_to_raw, producer_simulate
    "installs",
    "actions",
    "raw_actions",     # Debezium CDC -> Iceberg Sink
    "control-iceberg", # Iceberg Sink Connector
    "filebeat-logs"    # Filebeat
)

try {
    docker compose exec kafka true 2>$null
    if ($LASTEXITCODE -ne 0) { throw "kafka not running" }
} catch {
    Write-Host "Запустите стек: docker compose up -d"
    Write-Host "Пример вручную: docker compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic banner_events --partitions $Partitions --replication-factor $Replication --if-not-exists"
    exit 1
}

foreach ($topic in $topics) {
    docker compose exec kafka kafka-topics --create `
        --bootstrap-server localhost:9092 `
        --topic $topic `
        --partitions $Partitions `
        --replication-factor $Replication `
        --if-not-exists
    if ($LASTEXITCODE -eq 0) { Write-Host "Topic $topic OK" }
}

Write-Host "Готово. Список: docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092"
