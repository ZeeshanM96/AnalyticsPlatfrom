# pulsar_to_kafka.py
import os
import time
from pulsar import Client, ConsumerType
from confluent_kafka import Producer

# Load settings
PULSAR_URL = "pulsar://pulsar:6650"
PULSAR_CLEAN_TOPIC = os.getenv("PULSAR_CLEAN_TOPIC")
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC_CLEAN = os.getenv("EXTERNAL_TOPIC")
GROUP_ID_CLEAN = os.getenv("CONSUMER_GROUP_EXTERNAL")
PULSAR_DIRTY_TOPIC = os.getenv("PULSAR_DIRTY_TOPIC")
KAFKA_TOPIC_DIRTY = os.getenv("FAILED_TOPIC")
GROUP_ID_DIRTY = os.getenv("CONSUMER_GROUP_FAILED")


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


# Connect to Pulsar
def get_pulsar_client(pulsar_url: str, retries: int = 10, delay: int = 3) -> Client:
    for attempt in range(retries):
        try:
            return Client(pulsar_url)
        except Exception as e:
            print(f"🔄 Retrying Pulsar connection ({attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError(
        f"❌ Failed to connect to Pulsar at {pulsar_url} after {retries} attempts"
    )


# Consumers for both clean and dirty
client = get_pulsar_client(PULSAR_URL)
consumer_clean = setup_consumer(client, PULSAR_CLEAN_TOPIC, GROUP_ID_CLEAN)
consumer_dirty = setup_consumer(client, PULSAR_DIRTY_TOPIC, GROUP_ID_DIRTY)
# Set up Kafka producer
producer = Producer({"bootstrap.servers": KAFKA_BROKER})

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
                consumer.acknowledge(msg)
            except Exception as e:
                if "Timeout" not in str(e):
                    print(f"❌ Error in forwarding from {kafka_topic}: {e}")
except KeyboardInterrupt:
    print("🛑 Shutting down forwarder...")
finally:
    producer.flush()
    consumer_clean.close()
    consumer_dirty.close()
    client.close()
