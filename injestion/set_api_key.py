# injestion/set_api_key.py

import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
API_KEY = os.getenv("API_KEY")

try:
    REDIS_PORT = int(os.getenv("REDIS_PORT"))
except ValueError:
    raise ValueError("REDIS_PORT must be a valid integer")

if not all([REDIS_HOST, REDIS_PORT, API_KEY]):
    raise ValueError("REDIS_HOST, REDIS_PORT, and API_KEY must be set in the environment")

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
except redis.RedisError as e:
    raise RuntimeError(f"Failed to connect to Redis: {e}")


data = {
    "allowed": True,
    "source_ids": []
}

# Store in Redis if not already present
if not redis_client.exists(f"api_key:{API_KEY}"):
    redis_client.set(f"api_key:{API_KEY}", json.dumps(data))
    print("✅ API key saved to Redis.")
else:
    print("ℹ️ API key already exists in Redis.")
