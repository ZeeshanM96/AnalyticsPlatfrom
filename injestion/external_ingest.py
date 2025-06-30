# injestion/external_ingest.py
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, status
from datetime import timezone
from redis import Redis
from confluent_kafka import Producer
from backend.db import get_connection
import json
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
WS_TOPIC = os.getenv("WS_TOPIC")
DB_TOPIC = os.getenv("DB_TOPIC")
EXTERNAL_TOPIC = os.getenv("EXTERNAL_TOPIC")
REDIS_HOST = os.getenv("REDIS_HOST")

try:
    REDIS_PORT = int(os.getenv("REDIS_PORT"))
except ValueError:
    raise ValueError("REDIS_PORT must be a valid integer") from None

# Validate environment variables
required_vars = [KAFKA_BROKER, WS_TOPIC, DB_TOPIC, EXTERNAL_TOPIC, REDIS_HOST, REDIS_PORT]
if any(v is None for v in required_vars):
    raise ValueError(
        "Environment variables KAFKA_BROKER, WS_TOPIC, DB_TOPIC, EXTERNAL_TOPIC, REDIS_HOST, and REDIS_PORT must be set."
    )

producer = None
def get_producer():
    global producer
    if producer is None:
        try:
            producer = Producer({'bootstrap.servers': KAFKA_BROKER})
        except Exception as e:
            raise RuntimeError(f"Failed to create Kafka producer: {e}") from e
    return producer

def get_redis_client() -> Redis:
    try:
        client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping() 
        return client
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Redis: {e}") from e


def verify_api_key(api_key: str):
    redis_client = get_redis_client()
    record = redis_client.get(f"api_key:{api_key}")
    if not record:
        return None
    try:
        data = json.loads(record)
        return data if data.get("allowed", False) else None
    except json.JSONDecodeError:
        return None


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
                    await websocket.send_text("❌ Missing required fields: metric_name, value")
                    continue
                
                if "source_id" not in data:
                    await websocket.send_text("❌ Missing 'source_id' in message")
                    continue

                if str(data["source_id"]) not in [str(sid) for sid in source_ids]:
                    await websocket.send_text("❌ Unauthorized source_id")
                    continue
                
                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    cursor.execute("SELECT 1 FROM Sources WHERE SourceID = ?", (data["source_id"]))
                    if not cursor.fetchone():
                        await websocket.send_text("❌ Invalid source_id")
                        continue
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                data["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

                key = str(data["source_id"]).encode("utf-8")
                value = json.dumps(data).encode("utf-8")

                # Produce to Kafka
                producer = get_producer()
                producer.flush()

                await websocket.send_text("✅ Published to Kafka")
            except Exception as e:
                await websocket.send_text(f"❌ Error: {e}")
    except WebSocketDisconnect:
        print(f"Client disconnected")
