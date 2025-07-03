# pulsar_to_kafka.py
import os
import time
from pulsar import ConsumerType
from confluent_kafka import Producer
from pulsar_lib.pulsar_utils import get_pulsar_client

# Load settings
PULSAR_URL = os.getenv("PULSAR_URL", "pulsar://pulsar:6650")
PULSAR_CLEAN_TOPIC = os.getenv("PULSAR_CLEAN_TOPIC")
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC_CLEAN = os.getenv("EXTERNAL_TOPIC")
GROUP_ID_CLEAN = os.getenv("CONSUMER_GROUP_EXTERNAL")
PULSAR_DIRTY_TOPIC = os.getenv("PULSAR_DIRTY_TOPIC")
KAFKA_TOPIC_DIRTY = os.getenv("FAILED_TOPIC")
GROUP_ID_DIRTY = os.getenv("CONSUMER_GROUP_FAILED")

# Validate required environment variables
required_vars = {
    "PULSAR_CLEAN_TOPIC": PULSAR_CLEAN_TOPIC,
    "KAFKA_BROKER": KAFKA_BROKER,
    "EXTERNAL_TOPIC": KAFKA_TOPIC_CLEAN,
    "CONSUMER_GROUP_EXTERNAL": GROUP_ID_CLEAN,
    "PULSAR_DIRTY_TOPIC": PULSAR_DIRTY_TOPIC,
    "FAILED_TOPIC": KAFKA_TOPIC_DIRTY,
    "CONSUMER_GROUP_FAILED": GROUP_ID_DIRTY,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )


def setup_consumer(client, pulsar_topic, group_id):
    for attempt in range(10):
        try:
            return client.subscribe(
                pulsar_topic,
                subscription_name=group_id,
                consumer_type=ConsumerType.Shared,
            )
        except Exception as e:
            print(f"🔄 Retrying subscription to {pulsar_topic} ({attempt + 1}/10): {e}")
            time.sleep(3)
    raise RuntimeError(f"❌ Failed to subscribe to topic {pulsar_topic}")


try:
    client = get_pulsar_client(PULSAR_URL)
except Exception as e:
    print(f"❌ Failed to connect to Pulsar: {e}")
    raise

try:
    consumer_clean = setup_consumer(client, PULSAR_CLEAN_TOPIC, GROUP_ID_CLEAN)
except Exception as e:
    print(f"❌ Failed to subscribe to clean topic '{PULSAR_CLEAN_TOPIC}': {e}")
    raise

try:
    consumer_dirty = setup_consumer(client, PULSAR_DIRTY_TOPIC, GROUP_ID_DIRTY)
except Exception as e:
    print(f"❌ Failed to subscribe to dirty topic '{PULSAR_DIRTY_TOPIC}': {e}")
    raise

try:
    producer = Producer({"bootstrap.servers": KAFKA_BROKER})
except Exception as e:
    print(f"❌ Failed to initialize Kafka producer: {e}")
    raise

print(f"▶ Forwarding CLEAN: {PULSAR_CLEAN_TOPIC} → Kafka {KAFKA_TOPIC_CLEAN}")
print(f"▶ Forwarding DIRTY: {PULSAR_DIRTY_TOPIC} → Kafka {KAFKA_TOPIC_DIRTY}")


def delivery_report(err, msg):
    if err:
        print(f"❌ Kafka delivery failed: {err}")
    else:
        print(f"✅ Delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")


try:
    while True:
        for consumer, kafka_topic in [
            (consumer_clean, KAFKA_TOPIC_CLEAN),
            (consumer_dirty, KAFKA_TOPIC_DIRTY),
        ]:
            try:
                msg = consumer.receive(timeout_millis=1000)
                data = msg.data()
                producer.produce(kafka_topic, value=data, callback=delivery_report)
                producer.poll(0)
                try:
                    consumer.acknowledge(msg)
                except Exception as ack_err:
                    print(
                        f"⚠️ Failed to acknowledge message on {kafka_topic}: {ack_err}"
                    )
            except Exception as e:
                if "timeout" in type(e).__name__.lower():
                    continue
                print(f"❌ Error in forwarding from {kafka_topic}: {e}")

except KeyboardInterrupt:
    print("🛑 Shutting down forwarder...")

finally:
    producer.flush()
    consumer_clean.close()
    consumer_dirty.close()
    client.close()
