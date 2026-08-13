from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable

from src.ingest.sources.base import SourceSpec
from src.ingest.state import IngestState


CURRENCIES = ["USD", "EUR", "GBP"]
PAYMENT_STATUSES = ["succeeded", "failed", "refunded", "pending"]

PLAN_MONTHLY_PRICES = {
    "free": 0,
    "basic": 29,
    "pro": 99,
    "enterprise": 499
}

PAYMENT_METHODS = ["card", "paypal", "bank_transfer", "apple_pay", "google_pay"]


def _normal_random(mean: float, std: float, min_val: float = None, max_val: float = None) -> float:
    value = random.gauss(mean, std)
    if min_val is not None:
        value = max(value, min_val)
    if max_val is not None:
        value = min(value, max_val)
    return round(value, 2)


def _truncated_exponential(lam: float, min_val: float, max_val: float) -> float:
    value = random.expovariate(lam)
    return round(max(min_val, min(value, max_val)), 2)


class TransactionsSource:
    def __init__(self, num_users: int = 100, seed: int = 42):
        self.num_users = num_users
        self.seed = seed
        self._paid_user_ids = []
        self._user_plans = {}
        self._user_signup_dates = {}

    def spec(self) -> SourceSpec:
        return SourceSpec(
            source="saas",
            dataset="transactions",
            state_key="saas_transactions",
            enabled=True,
        )

    def extract(self, client, state: IngestState) -> Iterable[dict[str, Any]]:
        random.seed(self.seed)
        today = datetime.now(timezone.utc)
        
        self._paid_user_ids = [f"user_{i:05d}" for i in range(1, self.num_users + 1)]
        self._user_plans = {}
        self._user_signup_dates = {}
        
        for user_id in self._paid_user_ids:
            user_num = int(user_id.split("_")[1])
            signup_days_ago = int(-random.expovariate(0.02) + random.randint(10, 90))
            signup_days_ago = max(1, min(signup_days_ago, 180))
            self._user_signup_dates[user_id] = today - timedelta(days=signup_days_ago)
            
            plan = random.choices(
                ["basic", "pro", "enterprise"],
                weights=[0.55, 0.30, 0.15]
            )[0]
            self._user_plans[user_id] = plan
        
        transactions = []
        
        for user_id in self._paid_user_ids:
            plan = self._user_plans[user_id]
            signup_date = self._user_signup_dates[user_id]
            
            base_price = PLAN_MONTHLY_PRICES[plan]
            
            days_since_signup = (today - signup_date).days
            
            if days_since_signup < 7:
                continue
            
            num_payments = min(max(1, days_since_signup // 28), 12)
            
            first_payment = signup_date + timedelta(days=random.randint(1, 7))
            
            for p in range(num_payments):
                payment_date = first_payment + timedelta(days=p * 28 + random.randint(-2, 2))
                
                if payment_date > today:
                    break
                
                if plan == "basic":
                    amount = _truncated_exponential(lam=0.05, min_val=20, max_val=45)
                elif plan == "pro":
                    amount = _normal_random(mean=99, std=15, min_val=79, max_val=149)
                else:
                    amount = _normal_random(mean=499, std=50, min_val=399, max_val=699)
                
                currency = random.choices(CURRENCIES, weights=[0.70, 0.20, 0.10])[0]
                
                if p == 0:
                    status = random.choices(
                        PAYMENT_STATUSES,
                        weights=[0.85, 0.08, 0.02, 0.05]
                    )[0]
                else:
                    status = random.choices(
                        PAYMENT_STATUSES,
                        weights=[0.92, 0.03, 0.03, 0.02]
                    )[0]
                
                if status == "succeeded":
                    payment_method = random.choice(PAYMENT_METHODS)
                else:
                    payment_method = random.choice(PAYMENT_METHODS)
                
                transactions.append({
                    "transaction_id": None,
                    "user_id": user_id,
                    "amount": amount,
                    "currency": currency,
                    "status": status,
                    "payment_method": payment_method,
                    "plan": plan if status == "succeeded" else None,
                    "created_at": payment_date.isoformat(),
                    "description": f"Subscription payment - {plan} plan",
                })
        
        random.shuffle(transactions)
        
        for i, txn in enumerate(transactions[:500]):
            txn["transaction_id"] = f"txn_{i+1:06d}"
            txn["batch_id"] = today.strftime("%Y%m%d")
            yield txn

    def next_state(self, state: IngestState, records: list[dict[str, Any]]) -> IngestState:
        return state