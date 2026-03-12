-- Публикация для Debezium (Kafka Connect CDC): только таблицы, которые будем стримить в Kafka.
-- Требует wal_level=logical (в docker-compose для postgres задано: -c wal_level=logical).

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'dbz_publication') THEN
    CREATE PUBLICATION dbz_publication FOR TABLE ods.fct_actions;
  END IF;
END
$$;
