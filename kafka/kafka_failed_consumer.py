# kafka_failed_consumer.py
from confluent_kafka import Consumer
import json
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from kafka.kafka_handler import wait_for_kafka_ready, get_connection_with_retry
from backend.utils.db_utils import create_failed_metrics_table

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER")
FAILED_TOPIC = os.getenv("FAILED_TOPIC", "dirty-metrics")
CONSUMER_GROUP_FAILED = os.getenv("CONSUMER_GROUP_FAILED")


kafka_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": CONSUMER_GROUP_FAILED,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
}


wait_for_kafka_ready(
    bootstrap_servers=KAFKA_BROKER, retries=10, delay=5, initial_delay=5
)
consumer = Consumer(kafka_config)
consumer.subscribe([FAILED_TOPIC])

init_conn = get_connection_with_retry(retries=5, delay=5)
create_failed_metrics_table(init_conn)
init_conn.close()

print("🟢 Kafka Consumer FOR FAILED METRICS running...")


try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        conn = cursor = None
        try:
            data = json.loads(msg.value().decode("utf-8"))
            print(f"❗ Received dirty message: {data}")

            conn = get_connection_with_retry(retries=5, delay=5)
            cursor = conn.cursor()

            raw_data = {}
            try:
                raw_data = json.loads(data.get("raw", "{}"))
            except json.JSONDecodeError:
                pass

            timestamp_str = raw_data.get("timestamp")

            try:
                if timestamp_str:
                    dt_obj = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                    timestamp = dt_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                else:
                    timestamp = datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    )[:-3]
            except Exception:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[
                    :-3
                ]

            cursor.execute(
                """
                INSERT INTO FailedMetrics (source_id, metric_name, value, timestamp, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    raw_data.get("source_id"),
                    raw_data.get("metric_name"),
                    raw_data.get("value"),
                    timestamp,
                    data.get("error") or "Unknown error",
                ),
            )

            conn.commit()
        except Exception as e:
            print(f"❌ Insert failed dirty: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

except KeyboardInterrupt:
    print("Shutting down dirty consumer...")
finally:
    consumer.close()
