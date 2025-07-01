import websocket
import threading
import json
import time

url = "ws://localhost:8000/ws/ingest"

headers = [
    "x-source-id: 1",
    "x-api-key: API-KEY-FORSOURCE-1",
    "x-secret-key: SECRET-KEY-FORSOURCE-1",
]

payload = {"source_id": 1, "metric_name": "Humidity", "value": 23.9}


def on_message(ws, message):
    print("📥 Received:", message)


def on_error(ws, error):
    print("❌ Error:", error)


def on_close(ws, close_status_code, close_msg):
    print("🔌 Disconnected:", close_status_code, close_msg)


def on_open(ws):
    def send_loop():
        try:
            while True:
                ws.send(json.dumps(payload))
                print("📤 Sent:", payload)
                time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Send loop interrupted")
            ws.close()
        except Exception as e:
            print(f"❌ Send loop error: {e}")
            ws.close()

    thread = threading.Thread(target=send_loop, daemon=True)
    thread.start()


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        url,
        header=list(headers),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )

    websocket.enableTrace(False)
    ws.run_forever()
