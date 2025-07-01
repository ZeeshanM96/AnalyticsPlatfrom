# injestion/set_api_key.py
import json
from injestion.external_ingest import get_redis_client
from backend.utils.db_utils import get_all_keys
from backend.utils.db_conn import get_connection


def prewarm_api_credentials():
    redis_client = get_redis_client()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        all_keys = get_all_keys(cursor)

        for entry in all_keys:
            source_id = entry["source_id"]
            api_key = entry["api_key"]
            secret_key = entry["secret_key"]

            redis_key = f"api_key:{api_key}"
            redis_value = json.dumps(
                {"secret_key": secret_key, "source_id": source_id, "allowed": True}
            )

            redis_client.setex(redis_key, 3600, redis_value)
            print(f"✅ Cached API key for source_id={source_id}")

    finally:
        cursor.close()
        conn.close()
