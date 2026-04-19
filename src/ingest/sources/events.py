from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable

from src.ingest.sources.base import SourceSpec
from src.ingest.state import IngestState


EVENT_TYPES = [
    "login", "logout", "page_view", "api_call", "feature_use",
    "button_click", "form_submit", "search_query", "export_data",
    "payment", "upgrade", "downgrade", "cancel", "support_ticket",
    "invite_sent", "invite_accepted", "checkout_start", "checkout_complete"
]

EVENT_WEIGHTS = {
    "free": [0.25, 0.15, 0.30, 0.10, 0.08, 0.05, 0.03, 0.02, 0.01, 0.01],
    "basic": [0.20, 0.12, 0.25, 0.15, 0.10, 0.08, 0.04, 0.03, 0.02, 0.01],
    "pro": [0.15, 0.08, 0.20, 0.20, 0.12, 0.10, 0.05, 0.04, 0.03, 0.03],
    "enterprise": [0.10, 0.05, 0.15, 0.25, 0.15, 0.10, 0.08, 0.05, 0.04, 0.03]
}

EVENT_PROPERTIES = {
    "login": ["ip_country", "device_type", "method"],
    "logout": ["session_duration_minutes"],
    "page_view": ["url", "referrer", "device_type", "time_on_page"],
    "api_call": ["endpoint", "method", "status_code", "latency_ms"],
    "feature_use": ["feature_name", "feature_category"],
    "button_click": ["button_id", "button_text", "page_url"],
    "form_submit": ["form_id", "form_name", "success"],
    "search_query": ["query", "results_count"],
    "export_data": ["format", "record_count"],
    "payment": ["amount", "payment_method", "currency"],
    "upgrade": ["from_plan", "to_plan", "prorate_amount"],
    "downgrade": ["from_plan", "to_plan", "reason"],
    "cancel": ["reason", "feedback_provided"],
    "support_ticket": ["category", "priority", "status"],
    "invite_sent": ["email", "invite_type"],
    "invite_accepted": ["inviter_id"],
    "checkout_start": ["cart_total", "cart_items", "currency"],
    "checkout_complete": ["order_total", "payment_method", "coupon_used"]
}


class UserBehavior:
    def __init__(self, user_id: str, plan: str, signup_date: datetime):
        self.user_id = user_id
        self.plan = plan
        self.signup_date = signup_date
        self.last_event_date = signup_date
        self.event_count = 0
        self.is_churned = False
        self.is_upgraded = False
        
        if plan == "free":
            self.daily_event_rate = random.expovariate(0.3)
            self.churn_prob = 0.15
            self.upgrade_prob = 0.20
        elif plan == "basic":
            self.daily_event_rate = random.expovariate(0.5)
            self.churn_prob = 0.10
            self.upgrade_prob = 0.25
        elif plan == "pro":
            self.daily_event_rate = random.expovariate(0.8)
            self.churn_prob = 0.05
            self.upgrade_prob = 0.15
        else:
            self.daily_event_rate = random.expovariate(1.2)
            self.churn_prob = 0.02
            self.upgrade_prob = 0.05
    
    def should_churn(self) -> bool:
        if random.random() < self.churn_prob:
            self.is_churned = True
            return True
        return False
    
    def should_upgrade(self) -> bool:
        if not self.is_churned and not self.is_upgraded:
            if random.random() < self.upgrade_prob:
                self.is_upgraded = True
                return True
        return False
    
    def get_events_for_day(self, day: datetime) -> list[dict]:
        if day < self.signup_date:
            return []
        
        if self.is_churned and day > self.last_event_date + timedelta(days=7):
            return []
        
        events_today = max(1, int(random.gauss(self.daily_event_rate, self.daily_event_rate * 0.5)))
        events = []
        
        plan_weights = EVENT_WEIGHTS.get(self.plan, EVENT_WEIGHTS["free"])
        
        for _ in range(events_today):
            event_type = random.choices(EVENT_TYPES[:10], weights=plan_weights[:10])[0]
            
            hour = int(random.triangular(6, 22, 12))
            minute = random.randint(0, 59)
            timestamp = day.replace(hour=hour, minute=minute, second=random.randint(0, 59))
            
            properties = self._generate_properties(event_type)
            
            events.append({
                "event_id": None,
                "user_id": self.user_id,
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
                "properties": properties,
            })
            
            self.last_event_date = day
            self.event_count += 1
        
        return events
    
    def _generate_properties(self, event_type: str) -> dict:
        props = {}
        
        if event_type == "login":
            props = {
                "ip_country": random.choice(["US", "DE", "GB", "FR", "CA"]),
                "device_type": random.choices(["desktop", "mobile", "tablet"], weights=[0.60, 0.30, 0.10])[0],
                "method": random.choice(["password", "sso", "mfa"])
            }
        elif event_type == "page_view":
            props = {
                "url": random.choice(["/dashboard", "/pricing", "/features", "/docs", "/blog", "/settings", "/profile"]),
                "referrer": random.choice(["google", "direct", "twitter", "linkedin", None]),
                "device_type": random.choices(["desktop", "mobile", "tablet"], weights=[0.55, 0.35, 0.10])[0],
                "time_on_page": random.randint(5, 300)
            }
        elif event_type == "api_call":
            props = {
                "endpoint": random.choice(["/api/v1/users", "/api/v1/data", "/api/v1/analytics", "/api/v1/export"]),
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "status_code": random.choices([200, 201, 400, 401, 404, 500], weights=[0.75, 0.10, 0.08, 0.04, 0.02, 0.01])[0],
                "latency_ms": int(random.expovariate(0.01))
            }
        elif event_type == "feature_use":
            props = {
                "feature_name": random.choice(["analytics", "reports", "integrations", "automation", "api"]),
                "feature_category": random.choice(["core", "premium", "enterprise"])
            }
        elif event_type == "upgrade":
            from_plan = self.plan
            to_plan = random.choice([p for p in ["basic", "pro", "enterprise"] if p != from_plan])
            props = {
                "from_plan": from_plan,
                "to_plan": to_plan,
                "prorate_amount": round(random.uniform(10, 100), 2)
            }
        elif event_type == "cancel":
            props = {
                "reason": random.choice(["too_expensive", "not_used", "missing_features", "switching_competitor", "other"]),
                "feedback_provided": random.choice([True, False])
            }
        else:
            if event_type in EVENT_PROPERTIES:
                for prop in EVENT_PROPERTIES[event_type]:
                    if prop in ["latency_ms", "time_on_page"]:
                        props[prop] = random.randint(10, 500)
                    elif prop in ["cart_total", "order_total"]:
                        props[prop] = round(random.uniform(10, 500), 2)
                    elif prop in ["cart_items", "record_count"]:
                        props[prop] = random.randint(1, 50)
                    else:
                        props[prop] = f"value_{random.randint(1, 100)}"
        
        props["source"] = random.choices(["web", "mobile", "api"], weights=[0.70, 0.20, 0.10])[0]
        props["session_id"] = f"session_{random.randint(1, 100):03d}"
        
        return props


class EventsSource:
    def __init__(self, num_users: int = 100, seed: int = 42):
        self.num_users = num_users
        self.seed = seed

    def spec(self) -> SourceSpec:
        return SourceSpec(
            source="saas",
            dataset="events",
            state_key="saas_events",
            enabled=True,
        )

    def extract(self, client, state: IngestState) -> Iterable[dict[str, Any]]:
        random.seed(self.seed)
        today = datetime.now(timezone.utc)
        
        users_data = self._generate_users_data(today)
        
        all_events = []
        
        for user_data in users_data:
            behavior = UserBehavior(
                user_id=user_data["user_id"],
                plan=user_data["plan"],
                signup_date=user_data["signup_date"]
            )
            
            if behavior.should_upgrade():
                upgrade_event = self._create_upgrade_event(behavior, today)
                if upgrade_event:
                    all_events.append(upgrade_event)
            
            current_date = behavior.signup_date
            while current_date <= today:
                events = behavior.get_events_for_day(current_date)
                all_events.extend(events)
                
                if behavior.should_churn():
                    churn_event = self._create_churn_event(behavior, current_date)
                    if churn_event:
                        all_events.append(churn_event)
                    break
                
                current_date += timedelta(days=1)
        
        all_events.sort(key=lambda x: x["timestamp"])
        
        for i, event in enumerate(all_events):
            event["event_id"] = f"evt_{i+1:07d}"
            event["batch_id"] = today.strftime("%Y%m%d")
            yield event

    def _generate_users_data(self, today: datetime) -> list[dict]:
        users_data = []
        
        for i in range(1, self.num_users + 1):
            plan = random.choices(
                ["free", "basic", "pro", "enterprise"],
                weights=[0.60, 0.25, 0.10, 0.05]
            )[0]
            
            days_ago = int(-random.expovariate(0.02) + random.randint(5, 30))
            days_ago = max(1, min(days_ago, 180))
            signup_date = today - timedelta(days=days_ago)
            
            users_data.append({
                "user_id": f"user_{i:05d}",
                "plan": plan,
                "signup_date": signup_date
            })
        
        return users_data

    def _create_upgrade_event(self, behavior: UserBehavior, today: datetime) -> dict:
        upgrade_date = behavior.last_event_date + timedelta(days=random.randint(1, 14))
        
        if upgrade_date > today:
            return None
        
        to_plan = random.choice([p for p in ["basic", "pro", "enterprise"] if p != behavior.plan])
        
        return {
            "event_id": None,
            "user_id": behavior.user_id,
            "event_type": "upgrade",
            "timestamp": upgrade_date.isoformat(),
            "properties": {
                "from_plan": behavior.plan,
                "to_plan": to_plan,
                "prorate_amount": round(random.uniform(20, 150), 2),
                "source": "web",
                "session_id": f"session_{random.randint(1, 100):03d}"
            }
        }

    def _create_churn_event(self, behavior: UserBehavior, churn_date: datetime) -> dict:
        return {
            "event_id": None,
            "user_id": behavior.user_id,
            "event_type": "cancel",
            "timestamp": churn_date.isoformat(),
            "properties": {
                "reason": random.choice(["too_expensive", "not_used", "missing_features", "switching_competitor"]),
                "feedback_provided": random.choice([True, False]),
                "source": "web",
                "session_id": f"session_{random.randint(1, 100):03d}"
            }
        }

    def next_state(self, state: IngestState, records: list[dict[str, Any]]) -> IngestState:
        return state