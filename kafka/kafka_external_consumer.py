# kafka_external_consumer.py

from confluent_kafka import Consumer
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from kafka.kafka_handler import wait_for_kafka_ready, get_connection_with_retry


load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
EXTERNAL_TOPIC = os.getenv("EXTERNAL_TOPIC")
CONSUMER_GROUP_EXTERNAL = os.getenv("CONSUMER_GROUP_EXTERNAL")

# Validate environment variables
required_vars = [KAFKA_BROKER, EXTERNAL_TOPIC, CONSUMER_GROUP_EXTERNAL]
if any(v is None for v in required_vars):
    raise ValueError(
        "Environment variables KAFKA_BROKER, EXTERNAL_TOPIC, and "
        "CONSUMER_GROUP_EXTERNAL must be set."
    )


kafka_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": CONSUMER_GROUP_EXTERNAL,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
}

wait_for_kafka_ready(
    bootstrap_servers=KAFKA_BROKER, retries=10, delay=5, initial_delay=5
)
consumer = Consumer(kafka_config)
consumer.subscribe([EXTERNAL_TOPIC])

init_conn = get_connection_with_retry(retries=5, delay=5)
init_cursor = init_conn.cursor()

# Ensure ExternalSource table exists
init_cursor.execute(
    """
IF NOT EXISTS (
    SELECT * FROM sysobjects
    WHERE name='ExternalSource' AND xtype='U'
)
CREATE TABLE ExternalSource (
    id INT IDENTITY(1,1) PRIMARY KEY,
    source_id INT,
    metric_name VARCHAR(100),
    value FLOAT,
    timestamp DATETIME
)
"""
)
init_conn.commit()
init_conn.close()

print("🟢 External Kafka Consumer running...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Kafka error:", msg.error())
            continue

        data = None
        conn = None
        cursor = None
        try:
            data = json.loads(msg.value().decode("utf-8"))
            # Validate required fields
            required_fields = ["source_id", "metric_name", "value", "timestamp"]
            if not all(field in data for field in required_fields):
                print(f"❌ Missing required fields in message: {data}")
                continue

            try:
                data["timestamp"] = datetime.strptime(
                    data["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
                ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            except ValueError as ve:
                print(f"❌ Invalid timestamp format: {data['timestamp']} - {ve}")
                continue

            print(f"📥 Received: {data}")
            conn = get_connection_with_retry(retries=5, delay=5)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ExternalSource (source_id, metric_name, value, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                data["source_id"],
                data["metric_name"],
                data["value"],
                data["timestamp"],
            )
            conn.commit()

        except Exception as e:
            print(f"❌ DB Insert Error: {e} | Data: {data}")
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
        finally:
            try:
                if cursor:
                    cursor.close()
                    conn.close()
            except Exception:
                pass


except KeyboardInterrupt:
    print("Shutting down...")
finally:
    consumer.close()
