from __future__ import annotations

from src.ingest.sources.users import UsersSource
from src.ingest.sources.transactions import TransactionsSource
from src.ingest.sources.events import EventsSource


def build_sources():
    return [
        UsersSource(num_users=100, seed=42),
        TransactionsSource(num_users=100, seed=42),
        EventsSource(num_users=100, seed=42),
    ]
