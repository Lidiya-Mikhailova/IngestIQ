from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable

from src.ingest.sources.base import SourceSpec
from src.ingest.state import IngestState


SUBSCRIPTION_PLANS = ["free", "basic", "pro", "enterprise"]
PLAN_WEIGHTS = [0.60, 0.25, 0.10, 0.05]
PLAN_MONTHLY_PRICES = {"free": 0, "basic": 29, "pro": 99, "enterprise": 499}

COUNTRIES = ["US", "DE", "GB", "FR", "CA", "AU", "JP", "BR", "IN", "ES"]
COUNTRY_WEIGHTS = [0.30, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]

USER_STAGES = ["trial", "active", "churned"]
STAGE_WEIGHTS = [0.15, 0.70, 0.15]

FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
               "Kate", "Leo", "Maya", "Noah", "Olivia", "Paul", "Quinn", "Rose", "Sam", "Tara",
               "Victor", "Wendy", "Xavier", "Yara", "Zoe", "Anna", "Brian", "Chloe", "David", "Emma"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
              "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin",
              "Lee", "Thompson", "White", "Harris", "Clark", "Lewis", "Walker", "Hall", "Young"]


def _normal_random(mean: float, std: float, min_val: float = None, max_val: float = None) -> float:
    value = random.gauss(mean, std)
    if min_val is not None:
        value = max(value, min_val)
    if max_val is not None:
        value = min(value, max_val)
    return value


def _exponential_random(lam: float, max_val: float = None) -> float:
    value = -random.expovariate(lam)
    if max_val is not None:
        value = min(value, max_val)
    return abs(value)


def _generate_signup_date(today: datetime) -> datetime:
    days_ago = int(_exponential_random(lam=0.02, max_val=365))
    day = random.randint(1, 28)
    return (today - timedelta(days=days_ago)).replace(day=day, hour=random.randint(0, 23), minute=random.randint(0, 59))


def _generate_stage(plan: str, is_active: bool) -> str:
    if plan == "free":
        return random.choices(USER_STAGES, weights=[0.20, 0.50, 0.30])[0]
    elif plan == "enterprise":
        return random.choices(USER_STAGES, weights=[0.05, 0.90, 0.05])[0]
    else:
        return random.choices(USER_STAGES, weights=STAGE_WEIGHTS)[0]


class UsersSource:
    def __init__(self, num_users: int = 100, seed: int = 42):
        self.num_users = num_users
        self.seed = seed

    def spec(self) -> SourceSpec:
        return SourceSpec(
            source="saas",
            dataset="users",
            state_key="saas_users",
            enabled=True,
        )

    def extract(self, client, state: IngestState) -> Iterable[dict[str, Any]]:
        random.seed(self.seed)
        today = datetime.now(timezone.utc)
        
        generated_users = []
        
        for i in range(1, self.num_users + 1):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            plan = random.choices(SUBSCRIPTION_PLANS, weights=PLAN_WEIGHTS)[0]
            
            signup_date = _generate_signup_date(today)
            
            country = random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS)[0]
            
            if plan == "enterprise":
                is_active = random.choices([True, False], weights=[0.95, 0.05])[0]
            elif plan == "pro":
                is_active = random.choices([True, False], weights=[0.80, 0.20])[0]
            elif plan == "basic":
                is_active = random.choices([True, False], weights=[0.70, 0.30])[0]
            else:
                is_active = random.choices([True, False], weights=[0.50, 0.50])[0]
            
            stage = _generate_stage(plan, is_active)
            
            user = {
                "user_id": f"user_{i:05d}",
                "email": email,
                "name": f"{first_name} {last_name}",
                "signup_date": signup_date.isoformat(),
                "subscription_plan": plan,
                "is_active": is_active,
                "country": country,
                "stage": stage,
                "batch_id": today.strftime("%Y%m%d"),
            }
            generated_users.append(user)
            yield user

    def next_state(self, state: IngestState, records: list[dict[str, Any]]) -> IngestState:
        return state