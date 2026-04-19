from __future__ import annotations

import os
from pathlib import Path
import duckdb
from src.config.settings import app_settings as settings


def ensure_duckdb_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS saas_users (
            user_id VARCHAR PRIMARY KEY,
            email VARCHAR,
            name VARCHAR,
            signup_date TIMESTAMP,
            subscription_plan VARCHAR,
            is_active BOOLEAN,
            country VARCHAR,
            stage VARCHAR,
            batch_id VARCHAR
        )
    """)
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS saas_transactions (
            transaction_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            amount DECIMAL,
            currency VARCHAR,
            status VARCHAR,
            payment_method VARCHAR,
            plan VARCHAR,
            created_at TIMESTAMP,
            description VARCHAR,
            batch_id VARCHAR
        )
    """)
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS saas_events (
            event_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            event_type VARCHAR,
            timestamp TIMESTAMP,
            properties JSON,
            batch_id VARCHAR
        )
    """)
    
    con.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON saas_events(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON saas_events(event_type)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON saas_events(timestamp)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON saas_transactions(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_users_plan ON saas_users(subscription_plan)")


def load_to_duckdb() -> dict:
    raw_dir = settings.paths.raw_dir
    db_path = os.environ.get("DUCKDB_PATH", "data/warehouse.duckdb")
    
    con = duckdb.connect(db_path)
    
    ensure_duckdb_tables(con)
    
    con.execute("DELETE FROM saas_users")
    con.execute("DELETE FROM saas_transactions")
    con.execute("DELETE FROM saas_events")
    
    users_files = list(raw_dir.glob("source=saas/dataset=users/date=*/**/*.ndjson"))
    transactions_files = list(raw_dir.glob("source=saas/dataset=transactions/date=*/**/*.ndjson"))
    events_files = list(raw_dir.glob("source=saas/dataset=events/date=*/**/*.ndjson"))
    
    users_count = 0
    for f in users_files:
        result = con.execute(f"""
            INSERT INTO saas_users 
            SELECT 
                payload->>'user_id' AS user_id,
                payload->>'email' AS email,
                payload->>'name' AS name,
                CAST(payload->>'signup_date' AS TIMESTAMP) AS signup_date,
                payload->>'subscription_plan' AS subscription_plan,
                CAST(payload->>'is_active' AS BOOLEAN) AS is_active,
                payload->>'country' AS country,
                payload->>'stage' AS stage,
                payload->>'batch_id' AS batch_id
            FROM read_ndjson_auto('{f}')
        """)
        users_count += result.fetchone()[0] if hasattr(result, 'fetchone') else 0
    
    tx_count = 0
    for f in transactions_files:
        result = con.execute(f"""
            INSERT INTO saas_transactions
            SELECT 
                payload->>'transaction_id' AS transaction_id,
                payload->>'user_id' AS user_id,
                CAST(payload->>'amount' AS DECIMAL) AS amount,
                payload->>'currency' AS currency,
                payload->>'status' AS status,
                payload->>'payment_method' AS payment_method,
                payload->>'plan' AS plan,
                CAST(payload->>'created_at' AS TIMESTAMP) AS created_at,
                payload->>'description' AS description,
                payload->>'batch_id' AS batch_id
            FROM read_ndjson_auto('{f}')
        """)
        tx_count += result.fetchone()[0] if hasattr(result, 'fetchone') else 0
    
    events_count = 0
    for f in events_files:
        result = con.execute(f"""
            INSERT INTO saas_events
            SELECT 
                payload->>'event_id' AS event_id,
                payload->>'user_id' AS user_id,
                payload->>'event_type' AS event_type,
                CAST(payload->>'timestamp' AS TIMESTAMP) AS timestamp,
                payload->'properties' AS properties,
                payload->>'batch_id' AS batch_id
            FROM read_ndjson_auto('{f}')
        """)
        events_count += result.fetchone()[0] if hasattr(result, 'fetchone') else 0
    
    con.close()
    
    return {
        "users": users_count,
        "transactions": tx_count,
        "events": events_count
    }


if __name__ == "__main__":
    result = load_to_duckdb()
    print(f"Loaded: {result}")