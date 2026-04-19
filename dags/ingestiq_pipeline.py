from __future__ import annotations

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

ROOT = Path("/opt/airflow/ingestiq")
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.config.settings import DATABASE_URL, RAW_DIR
from src.orchestration.pipeline import run_pipeline
from src.transform.run import run_transform
from src.analytics.run import run_analytics

default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=2)
}

def ingest_task():
    logger.info("Starting ingest task")
    try:
        result = run_pipeline()
        logger.info("Ingest completed: %s", result)
        return "ok"
    except Exception as e:
        logger.exception("Ingest task failed: %s", e)
        raise

def transform_task():
    logger.info("Starting transform task")
    try:
        result = run_transform()
        logger.info("Transform completed: users=%s, transactions=%s, events=%s",
                    result.users_stage_rows, result.transactions_stage_rows, result.events_stage_rows)
        return "ok"
    except Exception as e:
        logger.exception("Transform task failed: %s", e)
        raise

def analytics_task():
    logger.info("Starting analytics task")
    try:
        result = run_analytics()
        logger.info("Analytics completed")
        return "ok"
    except Exception as e:
        logger.exception("Analytics task failed: %s", e)
        raise

with DAG(
    dag_id="ingestiq_pipeline",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    ingest = PythonOperator(
        task_id="ingest",
        python_callable=ingest_task,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task,
    )

    analytics = PythonOperator(
        task_id="analytics",
        python_callable=analytics_task,
    )

    ingest >> transform >> analytics
