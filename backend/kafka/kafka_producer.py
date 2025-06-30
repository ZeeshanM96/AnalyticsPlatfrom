# kafka_producer.py
from confluent_kafka import Producer
from backend.db import get_connection
import time
import json
import random
from datetime import datetime
import os
from dotenv import load_dotenv


load_dotenv()

# Load Kafka configuration from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
DB_TOPIC = os.getenv("DB_TOPIC")
WS_TOPIC = os.getenv("WS_TOPIC")
INTERVAL_SEC = float(os.getenv("PRODUCE_INTERVAL_SEC"))
MESSAGES_PER_SECOND = int(os.getenv("MESSAGES_PER_SECOND"))

# Ensure environment variables are set
required_vars = [KAFKA_BROKER, DB_TOPIC, WS_TOPIC, INTERVAL_SEC, MESSAGES_PER_SECOND]

if any(v is None for v in required_vars):
    raise ValueError(
        "KAFKA_BROKER, DB_TOPIC, WS_TOPIC, PRODUCE_INTERVAL_SEC, and "
        "MESSAGES_PER_SECOND must be set in .env"
    )

try:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Sources")
    source_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not source_ids:
        raise RuntimeError("❌ No source IDs found in Sources table.")
except Exception as e:
    print(f"❌ Failed to fetch source IDs from database: {e}")
    raise RuntimeError("Failed to initialize Kafka producer due to database connection issues")


def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")


producer = Producer({"bootstrap.servers": KAFKA_BROKER})


while True:
    for _ in range(MESSAGES_PER_SECOND):
        source_id = random.choice(source_ids)
        metric_name = "CPU_Usage" if source_id == 4 else "BatchCount"
        metric_value = (
            round(random.uniform(10.0, 95.0), 2)
            if source_id == 4
            else random.randint(5, 100)
        )
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")

        data = {
            "source_id": source_id,
            "metric_name": metric_name,
            "value": metric_value,
            "timestamp": timestamp,
        }

        key = str(source_id).encode("utf-8")
        value = json.dumps(data).encode("utf-8")

        producer.produce(DB_TOPIC, key=key, value=value, callback=delivery_report)
        producer.produce(WS_TOPIC, key=key, value=value, callback=delivery_report)

        producer.poll(0)

    print(f"Produced {MESSAGES_PER_SECOND} messages to each topic")
    time.sleep(INTERVAL_SEC)
