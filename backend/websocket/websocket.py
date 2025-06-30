# backend/websocket/websocket.py
from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi import APIRouter
from fastapi.security import HTTPBearer
from backend.utils.auth_utils import decode_jwt_token
from confluent_kafka import Consumer
from threading import Thread
import json
import asyncio
from backend.utils.db_conn import get_connection
from injestion.external_ingest import verify_api_key, get_producer
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# Load Kafka configuration from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
WS_TOPIC = os.getenv("WS_TOPIC")
CONSUMER_GROUP_WS = os.getenv("CONSUMER_GROUP_WS")
EXTERNAL_TOPIC = os.getenv("EXTERNAL_TOPIC")

# Ensure environment variables are set
required_vars = [KAFKA_BROKER, WS_TOPIC, CONSUMER_GROUP_WS, EXTERNAL_TOPIC]

if any(v is None for v in required_vars):
    raise ValueError(
        "KAFKA_BROKER, WS_TOPIC, EXTERNAL_TOPIC, CONSUMER_GROUP_WS must be set in .env"
    )

router = APIRouter()
security = HTTPBearer()


# Store connected WebSocket clients
connected_clients = []

kafka_consumer = Consumer(
    {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": f"{CONSUMER_GROUP_WS}_websocket",
        "auto.offset.reset": "latest",
    }
)
kafka_consumer.subscribe([WS_TOPIC])

try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


@router.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt")
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("user_id")
        email = payload.get("email")
    except Exception:
        await websocket.close(code=1008)
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        await websocket.close(code=1008)
        return

    source_id = row[0]
    await websocket.accept()
    print(f"Accepted connection for user {email} (source_id={source_id})")

    client = {"socket": websocket, "source_id": source_id}
    connected_clients.append(client)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {email}")
    finally:
        connected_clients.remove(client)


def kafka_listener():
    while True:
        msg = kafka_consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        try:
            data = json.loads(msg.value())
            partition = msg.partition()

            print(f"✅ WebSocket Kafka msg from partition {partition}: {data}")
            # Broadcast to all relevant WebSocket clients
            for client in connected_clients:
                if client["source_id"] == data["source_id"]:
                    asyncio.run_coroutine_threadsafe(
                        client["socket"].send_json(data), event_loop
                    )
        except Exception as e:
            print(f"Kafka/WebSocket broadcast error: {e}")


@router.websocket("/ws/ingest")
async def ingest_data(websocket: WebSocket):
    await websocket.accept()

    api_key = websocket.query_params.get("api_key")
    if not api_key:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    client_info = verify_api_key(api_key)
    if not client_info:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    source_ids = client_info.get("source_ids", [])
    await websocket.send_text(f"Authenticated as {source_ids}")

    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if "metric_name" not in data or "value" not in data:
                    await websocket.send_text(
                        "❌ Missing required fields: metric_name, value"
                    )
                    continue

                if "source_id" not in data:
                    await websocket.send_text("❌ Missing 'source_id' in message")
                    continue

                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT 1 FROM Sources WHERE SourceID = ?", (data["source_id"])
                    )
                    if not cursor.fetchone():
                        await websocket.send_text("❌ Invalid source_id")
                        continue
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                data["timestamp"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )

                key = str(data["source_id"]).encode("utf-8")
                value = json.dumps(data).encode("utf-8")

                # Produce to Kafka
                producer = get_producer()
                producer.produce(EXTERNAL_TOPIC, key=key, value=value)
                producer.flush()

                await websocket.send_text("✅ Published to Kafka")
            except Exception as e:
                await websocket.send_text(f"❌ Error: {e}")
    except WebSocketDisconnect:
        print("Client disconnected")


# Start Kafka listener in background thread
Thread(target=kafka_listener, daemon=True).start()
