#!/bin/bash
set -e
# Пользователь и пароль для Hive Metastore (apache/hive:4.0.0)
HIVE_PWD="${METASTORE_DB_PASSWORD:-metastore}"
# Экранируем одинарные кавычки для SQL (в Postgres: ' -> '')
HIVE_PWD_ESC=$(printf '%s' "$HIVE_PWD" | sed "s/'/''/g")
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
  CREATE USER hive WITH PASSWORD '${HIVE_PWD_ESC}';
  GRANT ALL PRIVILEGES ON DATABASE hivemeta TO hive;
  \c hivemeta
  GRANT ALL ON SCHEMA public TO hive;
EOSQL
