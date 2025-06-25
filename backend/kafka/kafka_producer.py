# kafka_producer.py
from confluent_kafka import Producer
import time, json, random
from datetime import datetime

producer = Producer({"bootstrap.servers": "kafka:9092"})

while True:
    source_id = random.choice([1, 2, 3, 4])
    metric_name = "CPU_Usage" if source_id == 4 else "BatchCount"
    value = (
        round(random.uniform(10.0, 95.0), 2)
        if source_id == 4
        else random.randint(5, 100)
    )
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
    data = {
        "source_id": source_id,
        "metric_name": metric_name,
        "value": value,
        "timestamp": timestamp,
    }

    producer.produce("db-topic", json.dumps(data).encode("utf-8"))
    producer.produce("websocket-topic", json.dumps(data).encode("utf-8"))
    producer.flush()
    print(f"Produced: {data}")
    time.sleep(5)
