#!/usr/bin/env bash

cd "$(dirname "$0")"

latest_log=$(find .airflow/logs/dag_id=ingestiq_pipeline -path "*/task_id=ingest/attempt=*.log" | sort | tail -n 1)

if [ -z "$latest_log" ]; then
  echo "Log file not found"
  exit 1
fi

echo "=== $latest_log ==="
sed -n '1,200p' "$latest_log"