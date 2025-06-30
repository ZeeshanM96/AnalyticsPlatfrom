# kafka_handler.py
from confluent_kafka import Consumer
import os
from dotenv import load_dotenv
import asyncio
import time
from backend.utils.db_conn import get_connection
from confluent_kafka.admin import AdminClient, NewTopic
import logging

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
WS_TOPIC = os.getenv("WS_TOPIC")
EXTERNAL_TOPIC = os.getenv("EXTERNAL_TOPIC")
CONSUMER_GROUP_WS = os.getenv("CONSUMER_GROUP_WS")
DB_TOPIC = os.getenv("DB_TOPIC")

if any(v is None for v in [KAFKA_BROKER, WS_TOPIC, CONSUMER_GROUP_WS, DB_TOPIC]):
    raise ValueError(
        "KAFKA_BROKER, WS_TOPIC, DB_TOPIC, CONSUMER_GROUP_WS must be set in .env"
    )

logger = logging.getLogger(__name__)

try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


kafka_consumer = Consumer(
    {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": f"{CONSUMER_GROUP_WS}_handler",
        "auto.offset.reset": "latest",
    }
)
kafka_consumer.subscribe([WS_TOPIC])


# Kafka topic check
def ensure_topic_exists(admin_client, topic_name):
    topics = admin_client.list_topics(timeout=5).topics
    if topic_name not in topics:
        logger.info(f"Creating Kafka topic: {topic_name}")
        admin_client.create_topics([NewTopic(topic_name, 1, 1)])
        time.sleep(1)


# Kafka readiness
def wait_for_kafka_ready(
    bootstrap_servers=KAFKA_BROKER, retries=10, delay=5, initial_delay=5
):
    if initial_delay > 0:
        time.sleep(initial_delay)
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
    ensure_topic_exists(admin_client, DB_TOPIC)
    for attempt in range(retries):
        try:
            cluster_metadata = admin_client.list_topics(timeout=5)
            if cluster_metadata.topics is not None:
                logger.info("Kafka is ready.")
                return
        except Exception as e:
            logger.warning(f"Waiting for Kafka... (attempt {attempt + 1}) -> {e}")
        time.sleep(delay)
    raise RuntimeError("Kafka is not ready after several retries.")


# Retry DB connection
def get_connection_with_retry(retries=5, delay=5):
    for attempt in range(retries):
        try:
            logger.info(f"Trying to connect to DB (attempt {attempt + 1}/{retries})...")
            return get_connection()
        except Exception as e:
            logger.warning(f"DB not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to DB after retries.")


def delivery_report(err, msg):
    if err is not None:
        logger.error(f"❌ Delivery failed: {err}")
    else:
        logger.info(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")
