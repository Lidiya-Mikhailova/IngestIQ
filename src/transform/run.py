from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from src.config.settings import app_settings as settings
from src.storage.postgres_client import PostgresClient

logger = logging.getLogger(__name__)


def _glob_ndjson(*, source: str, dataset_prefix: str) -> list[Path]:
    raw_dir = settings.paths.raw_dir
    base = raw_dir / f"source={source}"
    if not base.exists():
        return []

    files: list[Path] = []
    for dataset_dir in base.glob("dataset=*"):
        if dataset_dir.name.startswith("dataset=" + dataset_prefix):
            files.extend(dataset_dir.glob("date=*/**/*.ndjson"))
    return sorted(files)


def _ensure_stage_tables(db: PostgresClient) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS stg_users_raw (
            id SERIAL PRIMARY KEY,
            src_file VARCHAR,
            line_no INTEGER,
            ingested_at TIMESTAMP DEFAULT NOW(),
            payload JSONB
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS stg_transactions_raw (
            id SERIAL PRIMARY KEY,
            src_file VARCHAR,
            line_no INTEGER,
            ingested_at TIMESTAMP DEFAULT NOW(),
            payload JSONB
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS stg_events_raw (
            id SERIAL PRIMARY KEY,
            src_file VARCHAR,
            line_no INTEGER,
            ingested_at TIMESTAMP DEFAULT NOW(),
            payload JSONB
        )
    """)


def _ensure_marts(db: PostgresClient) -> None:
    db.execute("DROP TABLE IF EXISTS mart_users")
    db.execute("DROP TABLE IF EXISTS mart_transactions")
    db.execute("DROP TABLE IF EXISTS mart_events")

    db.execute("""
        CREATE TABLE mart_users (
            user_id VARCHAR PRIMARY KEY,
            email VARCHAR,
            name VARCHAR,
            signup_date TIMESTAMP,
            subscription_plan VARCHAR,
            is_active BOOLEAN,
            country VARCHAR,
            raw JSONB
        )
    """)

    db.execute("""
        CREATE TABLE mart_transactions (
            transaction_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            amount DECIMAL,
            currency VARCHAR,
            status VARCHAR,
            payment_method VARCHAR,
            plan VARCHAR,
            created_at TIMESTAMP,
            raw JSONB
        )
    """)

    db.execute("""
        CREATE TABLE mart_events (
            event_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            event_type VARCHAR,
            timestamp TIMESTAMP,
            properties JSONB,
            raw JSONB
        )
    """)

    db.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON mart_users(user_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_id ON mart_transactions(transaction_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_events_id ON mart_events(event_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON mart_transactions(user_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON mart_events(user_id)")


def _load_ndjson_into_stage(
    db: PostgresClient,
    *,
    table: str,
    files: list[Path],
) -> int:
    if not files:
        return 0

    total = 0
    for fpath in files:
        rows: list[tuple[str, int, str]] = []
        with fpath.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rows.append((str(fpath), i, json.dumps(obj, ensure_ascii=False)))

        if rows:
            db.executemany(
                f"""
                INSERT INTO {table} (src_file, line_no, ingested_at, payload)
                VALUES (:src_file, :line_no, NOW(), CAST(:payload AS JSONB))
                """,
                [{"src_file": r[0], "line_no": r[1], "payload": r[2]} for r in rows],
            )
            total += len(rows)

    return total


def _mart_users(db: PostgresClient) -> None:
    db.execute("""
        INSERT INTO mart_users (user_id, email, name, signup_date, subscription_plan, is_active, country, raw)
        SELECT DISTINCT ON (user_id)
            (payload->>'user_id')::VARCHAR AS user_id,
            (payload->>'email')::VARCHAR AS email,
            (payload->>'name')::VARCHAR AS name,
            CAST((payload->>'signup_date') AS TIMESTAMP) AS signup_date,
            (payload->>'subscription_plan')::VARCHAR AS subscription_plan,
            (payload->>'is_active')::BOOLEAN AS is_active,
            (payload->>'country')::VARCHAR AS country,
            payload AS raw
        FROM stg_users_raw
        WHERE payload->>'user_id' IS NOT NULL
        ON CONFLICT (user_id) DO UPDATE SET
            email = EXCLUDED.email,
            name = EXCLUDED.name,
            subscription_plan = EXCLUDED.subscription_plan,
            is_active = EXCLUDED.is_active,
            raw = EXCLUDED.raw
    """)


def _mart_transactions(db: PostgresClient) -> None:
    db.execute("""
        INSERT INTO mart_transactions (transaction_id, user_id, amount, currency, status, payment_method, plan, created_at, raw)
        SELECT DISTINCT ON (transaction_id)
            (payload->>'transaction_id')::VARCHAR AS transaction_id,
            (payload->>'user_id')::VARCHAR AS user_id,
            (payload->>'amount')::DECIMAL AS amount,
            (payload->>'currency')::VARCHAR AS currency,
            (payload->>'status')::VARCHAR AS status,
            (payload->>'payment_method')::VARCHAR AS payment_method,
            (payload->>'plan')::VARCHAR AS plan,
            CAST((payload->>'created_at') AS TIMESTAMP) AS created_at,
            payload AS raw
        FROM stg_transactions_raw
        WHERE payload->>'transaction_id' IS NOT NULL
        ON CONFLICT (transaction_id) DO UPDATE SET
            status = EXCLUDED.status,
            amount = EXCLUDED.amount,
            raw = EXCLUDED.raw
    """)


def _mart_events(db: PostgresClient) -> None:
    db.execute("""
        INSERT INTO mart_events (event_id, user_id, event_type, timestamp, properties, raw)
        SELECT DISTINCT ON (event_id)
            (payload->>'event_id')::VARCHAR AS event_id,
            (payload->>'user_id')::VARCHAR AS user_id,
            (payload->>'event_type')::VARCHAR AS event_type,
            CAST((payload->>'timestamp') AS TIMESTAMP) AS timestamp,
            payload->'properties' AS properties,
            payload AS raw
        FROM stg_events_raw
        WHERE payload->>'event_id' IS NOT NULL
        ON CONFLICT (event_id) DO UPDATE SET
            event_type = EXCLUDED.event_type,
            properties = EXCLUDED.properties,
            raw = EXCLUDED.raw
    """)


@dataclass(frozen=True)
class TransformResult:
    users_stage_rows: int
    transactions_stage_rows: int
    events_stage_rows: int
    users_mart_rows: int
    transactions_mart_rows: int
    events_mart_rows: int
    db_url: str


def run_transform() -> TransformResult:
    logger.info("Starting transform pipeline")
    logger.info("Raw dir path: %s", settings.paths.raw_dir)
    logger.info("Raw dir exists: %s", settings.paths.raw_dir.exists())
    
    db = PostgresClient.from_env()
    try:
        logger.info("Ensuring stage tables exist")
        _ensure_stage_tables(db)
        logger.info("Ensuring mart tables exist")
        _ensure_marts(db)

        logger.info("Clearing stage tables")
        db.execute("DELETE FROM stg_users_raw")
        db.execute("DELETE FROM stg_transactions_raw")
        db.execute("DELETE FROM stg_events_raw")

        logger.info("Globbing source files")
        users_files = _glob_ndjson(source="saas", dataset_prefix="users")
        transactions_files = _glob_ndjson(source="saas", dataset_prefix="transactions")
        events_files = _glob_ndjson(source="saas", dataset_prefix="events")
        
        logger.info("Found files - users: %d, transactions: %d, events: %d",
                    len(users_files), len(transactions_files), len(events_files))

        logger.info("Loading data into stage tables")
        n_users = _load_ndjson_into_stage(db, table="stg_users_raw", files=users_files)
        n_transactions = _load_ndjson_into_stage(db, table="stg_transactions_raw", files=transactions_files)
        n_events = _load_ndjson_into_stage(db, table="stg_events_raw", files=events_files)
        
        logger.info("Stage tables loaded - users: %d, transactions: %d, events: %d",
                    n_users, n_transactions, n_events)

        logger.info("Building mart tables")
        _mart_users(db)
        _mart_transactions(db)
        _mart_events(db)

        logger.info("Counting mart rows")
        users_cnt = db.execute_scalar("SELECT COUNT(*) FROM mart_users") or 0
        transactions_cnt = db.execute_scalar("SELECT COUNT(*) FROM mart_transactions") or 0
        events_cnt = db.execute_scalar("SELECT COUNT(*) FROM mart_events") or 0
        
        logger.info("Mart tables built - users: %d, transactions: %d, events: %d",
                    users_cnt, transactions_cnt, events_cnt)

        result = TransformResult(
            users_stage_rows=n_users,
            transactions_stage_rows=n_transactions,
            events_stage_rows=n_events,
            users_mart_rows=users_cnt,
            transactions_mart_rows=transactions_cnt,
            events_mart_rows=events_cnt,
            db_url="postgresql://postgres:***@postgres:5432/ingestiq_db",
        )
        logger.info("Transform pipeline completed successfully: %s", result)
        return result
    except Exception:
        logger.exception("Transform pipeline failed")
        raise
    finally:
        logger.info("Closing database connection")
        db.close()


if __name__ == "__main__":
    res = run_transform()
    print(res)
