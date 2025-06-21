from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter
from fastapi.security import HTTPBearer
from backend.auth import decode_jwt_token
import asyncio
from ..db import get_connection

router = APIRouter()
security = HTTPBearer()


@router.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket endpoint hit")
    token = websocket.query_params.get("token")
    print("Received token:", token)
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

    # Get user's source_id from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        await websocket.close(code=1008)
        return

    source_id = row[0]

    await websocket.accept()
    print(f"WebSocket accepted for user {email}, source_id={source_id}")

    last_event_id = 0
    try:
        while True:
            # Only fetch events from this user's source
            cursor.execute(
                """
                SELECT e.id, d.source_id, d.metric_name, d.value, d.timestamp
                FROM EventLog e
                JOIN RealTimeData d ON e.data_id = d.id
                WHERE e.id > ? AND d.source_id = ?
                ORDER BY e.id ASC
            """,
                last_event_id,
                source_id,
            )
            rows = cursor.fetchall()

            for row in rows:
                event_id, event_source_id, metric_name, value, timestamp = row
                last_event_id = event_id

                await websocket.send_json(
                    {
                        "id": event_id,
                        "source_id": event_source_id,
                        "metric_name": metric_name,
                        "value": value,
                        "timestamp": timestamp.isoformat(),
                    }
                )

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {email}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
