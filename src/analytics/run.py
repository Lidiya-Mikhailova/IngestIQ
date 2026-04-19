from src.analytics.summary import warehouse_summary, latest_timestamps


def run_analytics() -> None:
    print("\n=== WAREHOUSE SUMMARY ===\n")
    print(warehouse_summary())

    print("\n=== LATEST TIMESTAMPS ===\n")
    print(latest_timestamps())


if __name__ == "__main__":
    run_analytics()
