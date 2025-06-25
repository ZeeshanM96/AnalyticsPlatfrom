# websocket_kafka.py
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter
from fastapi.security import HTTPBearer
from backend.auth import decode_jwt_token
from confluent_kafka import Consumer
from threading import Thread
import json
import asyncio
from backend.db import get_connection


router = APIRouter()
security = HTTPBearer()


# Store connected WebSocket clients
connected_clients = []

kafka_consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'websocket-group',
    'auto.offset.reset': 'latest'
})
kafka_consumer.subscribe(['websocket-topic'])

event_loop = asyncio.get_event_loop()

@router.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt")
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("user_id")
        email = payload.get("email")
    except Exception:
        await websocket.close(code=1008)
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        await websocket.close(code=1008)
        return

    source_id = row[0]
    await websocket.accept()
    print(f"Accepted connection for user {email} (source_id={source_id})")

    client = {"socket": websocket, "source_id": source_id}
    connected_clients.append(client)

    try:
        while True:
            await asyncio.sleep(1)  # keep connection alive
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {email}")
    finally:
        connected_clients.remove(client)

def kafka_listener():
    while True:
        msg = kafka_consumer.poll(1.0)
        if msg is None or msg.error():
            continue
        try:
            data = json.loads(msg.value())
            # Broadcast to all relevant WebSocket clients
            for client in connected_clients:
                if client["source_id"] == data["source_id"]:
                    asyncio.run_coroutine_threadsafe(client["socket"].send_json(data), event_loop)
        except Exception as e:
            print(f"Kafka/WebSocket broadcast error: {e}")


# Start Kafka listener in background thread
Thread(target=kafka_listener, daemon=True).start()