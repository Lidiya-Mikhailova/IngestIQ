from __future__ import annotations

import argparse
import subprocess

from src.analytics.preview import preview
from src.analytics.run import run_analytics
from src.orchestration.pipeline import run_pipeline
from src.transform.run import run_transform


def main() -> None:
    parser = argparse.ArgumentParser(prog="ingestiq")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("all")
    subparsers.add_parser("ingest")
    subparsers.add_parser("transform")
    subparsers.add_parser("preview")
    subparsers.add_parser("analytics")
    subparsers.add_parser("dashboard")

    args = parser.parse_args()

    if args.command == "all":
        run_pipeline()
        result = run_transform()
        print(f"Transform: {result.users_mart_rows} users, {result.transactions_mart_rows} transactions, {result.events_mart_rows} events")
        run_analytics()

    elif args.command == "ingest":
        run_pipeline()

    elif args.command == "transform":
        result = run_transform()
        print(f"Transform: {result.users_mart_rows} users, {result.transactions_mart_rows} transactions, {result.events_mart_rows} events")

    elif args.command == "preview":
        preview()

    elif args.command == "analytics":
        run_analytics()

    elif args.command == "dashboard":
        try:
            subprocess.run(
                ["streamlit", "run", "src/dashboard/app.py"],
                check=False,
            )
        except KeyboardInterrupt:
            print("\nDashboard stopped.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
