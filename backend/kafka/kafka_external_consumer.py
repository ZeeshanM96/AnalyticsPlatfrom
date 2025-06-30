# kafka_external_consumer.py

from confluent_kafka import Consumer
import json
import time
from backend.db import get_connection
from confluent_kafka.admin import AdminClient, NewTopic
from datetime import datetime
import os
from dotenv import load_dotenv

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


# Retry DB connection
def get_connection_with_retry(retries=5, delay=5):
    """
    Attempt to establish a database connection, retrying multiple times with a delay between attempts.
    
    Parameters:
        retries (int): Maximum number of connection attempts.
        delay (int): Seconds to wait between retries.
    
    Returns:
        A database connection object if successful.
    
    Raises:
        Exception: If unable to connect after all retries.
    """
    for attempt in range(retries):
        try:
            print(f"Connecting to DB (attempt {attempt + 1})...")
            return get_connection()
        except Exception as e:
            print(f"DB not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to DB")


# Kafka topic check
def ensure_topic_exists(admin_client, topic_name):
    """
    Ensure that a Kafka topic exists, creating it if necessary.
    
    If the specified topic does not exist, it is created with one partition and a replication factor of one.
    """
    topics = admin_client.list_topics(timeout=5).topics
    if topic_name not in topics:
        print(f"Creating Kafka topic: {topic_name}")
        admin_client.create_topics([NewTopic(topic_name, 1, 1)])
        time.sleep(1)


# Kafka readiness
def wait_for_kafka_ready():
    """
    Waits for Kafka to become ready and ensures the external topic exists.
    
    This function pauses execution to allow Kafka services to initialize, then creates an AdminClient and verifies that the required external topic is present, creating it if necessary.
    """
    time.sleep(10)
    admin = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    ensure_topic_exists(admin, EXTERNAL_TOPIC)


kafka_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": CONSUMER_GROUP_EXTERNAL,
    "auto.offset.reset": "earliest",
}

wait_for_kafka_ready()
consumer = Consumer(kafka_config)
consumer.subscribe([EXTERNAL_TOPIC])

init_conn = get_connection_with_retry()
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
            conn = get_connection_with_retry()
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
                conn.rollback()
            except Exception:
                pass
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass


except KeyboardInterrupt:
    print("Shutting down...")
finally:
    consumer.close()
    conn.close()
