#!/usr/bin/env bash

cd "$(dirname "$0")"



export AIRFLOW_HOME="$(pwd)/.airflow"
export PYTHONPATH="$(pwd)"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__LOGGING__BASE_LOG_FOLDER="$AIRFLOW_HOME/logs"

mkdir -p "$AIRFLOW_HOME/logs"

airflow standalone