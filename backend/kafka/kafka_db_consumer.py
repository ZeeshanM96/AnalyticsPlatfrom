# Kafka DB Consumer
from confluent_kafka import Consumer
import json
import time
from backend.db import get_connection
from confluent_kafka.admin import AdminClient, NewTopic
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
# Load Kafka configuration from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
DB_TOPIC = os.getenv("DB_TOPIC")
CONSUMER_GROUP_DB=os.getenv("CONSUMER_GROUP_DB")
# Ensure environment variables are set
required_vars = [KAFKA_BROKER, DB_TOPIC, CONSUMER_GROUP_DB]
if any(v is None for v in required_vars):
    raise ValueError("KAFKA_BROKER, DB_TOPIC, CONSUMER_GROUP_DB must be set in .env")



# Retry DB connection
def get_connection_with_retry(retries=5, delay=5):
    for attempt in range(retries):
        try:
            print(f"Trying to connect to DB (attempt {attempt + 1}/{retries})...")
            return get_connection()
        except Exception as e:
            print(f"DB not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to DB after retries.")


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


def ensure_topic_exists(admin_client, topic_name):
    topics = admin_client.list_topics(timeout=5).topics
    if topic_name not in topics:
        print(f"Creating Kafka topic: {topic_name}")
        admin_client.create_topics(
            [NewTopic(topic_name, num_partitions=4, replication_factor=1)]
        )
        time.sleep(1)


def wait_for_kafka_ready(bootstrap_servers=KAFKA_BROKER, retries=10, delay=5):
    time.sleep(10)
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
    ensure_topic_exists(admin_client, DB_TOPIC)
    for attempt in range(retries):
        try:
            cluster_metadata = admin_client.list_topics(timeout=5)
            if cluster_metadata.topics is not None:
                print("Kafka is ready.")
                return
        except Exception as e:
            print(f"Waiting for Kafka... (attempt {attempt + 1}) -> {e}")
        time.sleep(delay)
    raise RuntimeError("Kafka is not ready after several retries.")


# Kafka config
kafka_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": CONSUMER_GROUP_DB,
    "auto.offset.reset": "earliest",
}

wait_for_kafka_ready()
consumer = create_kafka_consumer_with_retry(kafka_config, DB_TOPIC)
conn = get_connection_with_retry()
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
                data["source_id"],
                data["metric_name"],
                data["value"],
                data["timestamp"],
            )
            conn.commit()
        except Exception as e:
            print(f"DB Insert Error: {e}")
            conn.rollback()

except KeyboardInterrupt:
    print("Shutting down...")
finally:
    consumer.close()
    conn.close()
