# injestion/external_ingest.py
from fastapi import APIRouter
from redis import Redis
from confluent_kafka import Producer
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
