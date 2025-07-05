# pulsar/validate.py
# pulsar function
import json

PULSAR_CLEAN_TOPIC = "persistent://public/default/clean"
PULSAR_DIRTY_TOPIC = "persistent://public/default/dirty"

ALLOWED_METRICS = {"Humidity", "Temperature", "Logins", "CPU-Usage"}


def validate_payload(raw_msg):
    try:
        data = json.loads(raw_msg)
    except Exception as e:
        return False, {"raw": raw_msg, "error": f"Invalid JSON: {str(e)}"}

    try:
        # Extract + clean fields
        source_id = data.get("source_id")
        metric_name = str(data.get("metric_name", "")).strip()
        value = data.get("value")

        # Validation rules
        if not isinstance(source_id, int):
            raise ValueError("source_id must be int.")

        if metric_name not in ALLOWED_METRICS:
            raise ValueError(f"metric_name must be one of {ALLOWED_METRICS}")

        if not isinstance(value, (int, float)):
            raise ValueError("value must be int or float.")

        # Cleaned payload
        data["metric_name"] = metric_name
        return True, data

    except Exception as e:
        return False, {"raw": raw_msg, "error": str(e)}


class Validator:
    def process(self, input, context):
        if isinstance(input, bytes):
            input = input.decode("utf-8")
        is_valid, result = validate_payload(input)
        topic = PULSAR_CLEAN_TOPIC if is_valid else PULSAR_DIRTY_TOPIC
        print("✅ Clean:", result) if is_valid else print("❌ Invalid:", result)
        context.publish(topic, json.dumps(result))
