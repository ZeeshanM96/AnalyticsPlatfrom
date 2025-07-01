# injestion/external_ingest.py
from fastapi import APIRouter
from redis import Redis
from confluent_kafka import Producer
import json
import os
from dotenv import load_dotenv
from backend.utils.db_conn import get_connection
from backend.utils.db_utils import get_api_credentials
from typing import Optional

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
required_vars = [
    KAFKA_BROKER,
    WS_TOPIC,
    DB_TOPIC,
    EXTERNAL_TOPIC,
    REDIS_HOST,
    REDIS_PORT,
]
if any(v is None for v in required_vars):
    raise ValueError(
        "Environment variables KAFKA_BROKER, WS_TOPIC, DB_TOPIC, EXTERNAL_TOPIC, "
        "REDIS_HOST, and REDIS_PORT must be set."
    )

producer = None


def get_producer():
    global producer
    if producer is None:
        try:
            producer = Producer({"bootstrap.servers": KAFKA_BROKER})
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


def verify_api_key_with_source(
    source_id: int, api_key: str, secret_key: str
) -> Optional[dict]:
    redis_client = get_redis_client()
    cache_key = f"api_key:{api_key}"

    record = redis_client.get(cache_key)
    if record:
        try:
            data = json.loads(record)
            if (
                not data.get("allowed", False)
                or data.get("secret_key") != secret_key
                or str(data.get("source_id")) != str(source_id)
            ):
                return None
            return data
        except json.JSONDecodeError:
            return None

    # Fallback to DB
    try:
        conn = get_connection()
        cursor = conn.cursor()
        creds = get_api_credentials(cursor, int(source_id))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if creds["api_key"] != api_key or creds["secret_key"] != secret_key:
        return None

    # Store in Redis
    redis_client.setex(
        cache_key,
        3600,  # 1-hour TTL
        json.dumps(
            {"secret_key": secret_key, "source_id": int(source_id), "allowed": True}
        ),
    )

    return {"secret_key": secret_key, "source_id": int(source_id), "allowed": True}
