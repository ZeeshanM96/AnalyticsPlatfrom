# pulsar_lib/pulsar_utils.py
import os
import time
import pulsar
from typing import Optional

PULSAR_SERVICE_URL = os.getenv("PULSAR_SERVICE_URL", "pulsar://pulsar:6650")
RAW_TOPIC = os.getenv("RAW_TOPIC")

if not RAW_TOPIC:
    raise RuntimeError(
        "RAW_TOPIC environment variable not set – cannot create Pulsar producer"
    )

_client: Optional[pulsar.Client] = None
_producer: Optional[pulsar.Producer] = None


def get_pulsar_client(
    pulsar_url: str = PULSAR_SERVICE_URL, retries: int = 0, delay: int = 3
) -> pulsar.Client:
    global _client
    if _client:
        return _client

    for attempt in range(retries + 1):  # run once even if retries == 0
        try:
            _client = pulsar.Client(pulsar_url)
            return _client
        except Exception as e:
            if attempt == retries:
                break
            print(f"🔄 Retrying Pulsar connection ({attempt + 1}/{retries}): {e}")
            time.sleep(delay)

    raise RuntimeError(
        f"❌ Failed to connect to Pulsar at {pulsar_url} after {retries} attempts"
    )


def get_pulsar_producer() -> pulsar.Producer:
    global _producer
    if _producer is None:
        client = get_pulsar_client()
        _producer = client.create_producer(RAW_TOPIC)
    return _producer
