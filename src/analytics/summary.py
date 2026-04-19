from src.storage.postgres_client import PostgresClient


def warehouse_summary():
    db = PostgresClient.from_env()
    df = db.execute_df("""
        SELECT schemaname, relname AS table_name, n_live_tup AS rows_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY relname
    """)
    return df


def latest_timestamps():
    db = PostgresClient.from_env()
    df = db.execute_df("""
        SELECT 'mart_users' AS table_name, MAX(signup_date) AS latest_ts FROM mart_users
        UNION ALL
        SELECT 'mart_transactions', MAX(created_at) FROM mart_transactions
        UNION ALL
        SELECT 'mart_events', MAX(timestamp) FROM mart_events
        ORDER BY table_name
    """)
    return df


if __name__ == "__main__":
    print("\nWAREHOUSE SUMMARY\n")
    print(warehouse_summary())

    print("\nLATEST TIMESTAMPS\n")
    print(latest_timestamps())
