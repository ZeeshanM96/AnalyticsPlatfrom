# Kafka DB Consumer
from confluent_kafka import Consumer
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from kafka.kafka_handler import get_connection_with_retry, wait_for_kafka_ready

load_dotenv()
# Load Kafka configuration from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
DB_TOPIC = os.getenv("DB_TOPIC")
CONSUMER_GROUP_DB = os.getenv("CONSUMER_GROUP_DB")
# Ensure environment variables are set
required_vars = [KAFKA_BROKER, DB_TOPIC, CONSUMER_GROUP_DB]
if any(v is None for v in required_vars):
    raise ValueError("KAFKA_BROKER, DB_TOPIC, CONSUMER_GROUP_DB must be set in .env")


# Retry Kafka consumer setup
def create_kafka_consumer_with_retry(config, topic, retries=5, delay=5):
    for attempt in range(retries):
        try:
            print(f"Trying to connect to Kafka (attempt {attempt + 1}/{retries})...")
            consumer = Consumer(config)
            consumer.subscribe([topic])
            print("Kafka consumer connected and subscribed.")
            return consumer
        except Exception as e:
            print(f"Kafka not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to Kafka after retries.")


# Kafka config
kafka_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": CONSUMER_GROUP_DB,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
}

wait_for_kafka_ready(
    bootstrap_servers=KAFKA_BROKER, retries=10, delay=5, initial_delay=5
)
consumer = create_kafka_consumer_with_retry(kafka_config, DB_TOPIC)
conn = get_connection_with_retry(retries=5, delay=5)
cursor = conn.cursor()

# Ensure table exists
cursor.execute(
    """
IF NOT EXISTS (
    SELECT * FROM sysobjects
    WHERE name='RealTimeData' AND xtype='U'
)
CREATE TABLE RealTimeData (
    id INT IDENTITY(1,1) PRIMARY KEY,
    source_id INT,
    metric_name VARCHAR(100),
    value FLOAT,
    timestamp DATETIME
)
"""
)
conn.commit()

print("Kafka DB Consumer is running and listening...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            print("No message received.")
            continue
        if msg.error():
            print("Kafka error:", msg.error())
            continue

        try:
            data = json.loads(msg.value().decode("utf-8"))
            data["timestamp"] = datetime.strptime(
                data["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
            ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            print(f"✅ Received from partition {msg.partition()}: {data}")
            print(f"Inserting into DB: {data}")
            cursor.execute(
                """
                INSERT INTO RealTimeData (source_id, metric_name, value, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    data["source_id"],
                    data["metric_name"],
                    data["value"],
                    data["timestamp"],
                ),
            )
            conn.commit()
        except Exception as e:
            print(f"❌ Error processing message: {msg.value()}")
            print(f"DB Insert Error: {e}")
            conn.rollback()

except KeyboardInterrupt:
    print("Shutting down...")
finally:
    consumer.close()
    conn.close()
