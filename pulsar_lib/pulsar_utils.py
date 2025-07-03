# pulsar/pusar_utils.py
# Pulsar Producer Helper
import pulsar
import os

PULSAR_SERVICE_URL = "pulsar://pulsar:6650"
RAW_TOPIC = os.getenv("RAW_TOPIC")

_client = None
_producer = None


def get_pulsar_client():
    global _client
    if _client is None:
        _client = pulsar.Client(PULSAR_SERVICE_URL)
    return _client


def get_pulsar_producer():
    global _producer
    if _producer is None:
        client = get_pulsar_client()
        _producer = client.create_producer(RAW_TOPIC)
    return _producer
