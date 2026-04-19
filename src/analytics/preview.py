from src.storage.postgres_client import PostgresClient


def preview():
    db = PostgresClient.from_env()
    print("MART TABLES:")
    tables = db.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    print([row[0] for row in tables] if tables else [])

    print("\nUsers (mart_users):")
    print(db.execute_df("SELECT * FROM mart_users LIMIT 5"))

    print("\nTransactions (mart_transactions):")
    print(db.execute_df("SELECT * FROM mart_transactions LIMIT 5"))

    print("\nEvents (mart_events):")
    print(db.execute_df("SELECT * FROM mart_events LIMIT 5"))


if __name__ == "__main__":
    preview()
