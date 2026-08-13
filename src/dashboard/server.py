import asyncio
import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DASHBOARD_DIR = Path(__file__).resolve().parent
DASHBOARD_HTML = DASHBOARD_DIR / "dashboard.html"

EVENT_TYPES = [
    "page_view", "button_click", "form_submit", "login", "logout",
    "signup", "checkout_start", "checkout_complete", "subscription_upgrade",
    "subscription_cancel", "api_call", "search_query"
]

PLANS = ["free", "basic", "pro", "enterprise"]
PAYMENT_METHODS = ["card", "paypal", "bank_transfer", "apple_pay", "google_pay"]
STATUSES = ["succeeded", "failed", "refunded", "pending"]


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    def _generate_users_data(self) -> dict:
        return {
            "source": "users",
            "timestamp": datetime.now().isoformat(),
            "data": [
                {
                    "user_id": f"user_{i:05d}",
                    "name": f"User {i}",
                    "subscription_plan": random.choice(PLANS),
                    "is_active": random.random() < 0.8,
                    "country": random.choice(["US", "DE", "GB", "FR", "CA", "AU"]),
                }
                for i in range(1, 11)
            ],
        }

    def _generate_transactions_data(self) -> dict:
        return {
            "source": "transactions",
            "timestamp": datetime.now().isoformat(),
            "data": [
                {
                    "transaction_id": f"txn_{random.randint(100000, 999999)}",
                    "user_id": f"user_{random.randint(1, 100):05d}",
                    "amount": random.choice([29, 49, 99, 199, 499]),
                    "currency": random.choice(["USD", "EUR", "GBP"]),
                    "status": random.choices(STATUSES, weights=[0.75, 0.1, 0.05, 0.1])[0],
                    "payment_method": random.choice(PAYMENT_METHODS),
                }
                for _ in range(10)
            ],
        }

    def _generate_events_data(self) -> dict:
        return {
            "source": "events",
            "timestamp": datetime.now().isoformat(),
            "data": [
                {
                    "event_id": f"evt_{random.randint(1000000, 9999999)}",
                    "user_id": f"user_{random.randint(1, 100):05d}",
                    "event_type": random.choice(EVENT_TYPES),
                    "properties": {
                        "source": random.choice(["web", "mobile"]),
                        "session_id": f"session_{random.randint(1, 50):03d}",
                    },
                }
                for _ in range(15)
            ],
        }

    async def broadcast_loop(self):
        while True:
            data = self._generate_users_data()
            await self.broadcast(data)
            await asyncio.sleep(2)

            data = self._generate_transactions_data()
            await self.broadcast(data)
            await asyncio.sleep(2)

            data = self._generate_events_data()
            await self.broadcast(data)
            await asyncio.sleep(3)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(manager.broadcast_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to IngestIQ Dashboard",
            "timestamp": datetime.now().isoformat()
        })
        while True:
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
async def get_dashboard():
    if not DASHBOARD_HTML.exists():
        return {"error": "dashboard.html not found"}
    return FileResponse(DASHBOARD_HTML)


@app.get("/data/all")
async def get_all_data():
    return {
        "users": manager._generate_users_data(),
        "transactions": manager._generate_transactions_data(),
        "events": manager._generate_events_data(),
    }


if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()
