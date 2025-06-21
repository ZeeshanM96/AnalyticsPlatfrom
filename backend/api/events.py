# backend/api/events.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..auth import decode_jwt_token, is_admin, validate_date_range
from ..db import get_connection
from datetime import date, timedelta
from collections import defaultdict

router = APIRouter()
security = HTTPBearer()


@router.get("/geteventtypes")
def get_event_types(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")

    source_id = row[0]

    if is_admin(source_id):
        cursor.execute("SELECT DISTINCT EventType FROM Events")
    else:
        cursor.execute(
            "SELECT DISTINCT EventType FROM Events WHERE SourceID = ?", (source_id,)
        )

    return {"eventTypes": [row[0] for row in cursor.fetchall()]}


@router.get("/geteventtrends/")
def get_event_summary(
    from_date: str,
    to_date: str,
    events: str = "",
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    validate_date_range(from_date, to_date)
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")

    source_id = row[0]
    event_types = [e.strip() for e in events.split(",") if e.strip()]

    if not event_types:
        raise HTTPException(
            status_code=400, detail="At least one event type is required."
        )

    placeholders = ", ".join("?" for _ in event_types)
    params = [from_date, to_date] + event_types

    if is_admin(source_id):
        source_clause = "1=1"
    else:
        source_clause = "SourceID = ?"
        params = [source_id] + params

    cursor.execute(
        f"""
        SELECT
            CONVERT(date, EventTime) AS EventDate,
            EventType,
            COUNT(*) AS Count
        FROM Events
        WHERE {source_clause}
          AND EventTime BETWEEN ? AND ?
          AND EventType IN ({placeholders})
        GROUP BY CONVERT(date, EventTime), EventType
        ORDER BY EventDate, EventType
    """,
        params,
    )

    rows = cursor.fetchall()
    data = defaultdict(lambda: defaultdict(int))
    all_dates = set()

    for date_val, event_type, count in rows:
        date_str = date_val.strftime("%Y-%m-%d")
        data[event_type][date_str] = count
        all_dates.add(date_str)

    sorted_dates = sorted(all_dates)
    datasets = []

    for event_type, date_counts in data.items():
        datasets.append(
            {
                "label": event_type,
                "data": [date_counts.get(date, 0) for date in sorted_dates],
                "fill": False,
                "borderWidth": 2,
            }
        )

    return {"labels": sorted_dates, "datasets": datasets}


@router.get("/getbatchstatus")
def get_batch_counts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")

    source_id = row[0]
    today = date.today()
    yesterday = today - timedelta(days=1)

    base_query = """
        SELECT
            CAST(EventTime AS DATE) as event_date,
            COUNT(DISTINCT BatchID)
        FROM Events
        WHERE BatchID IS NOT NULL
          AND EventTime >= ? AND EventTime < ?
    """
    params = [yesterday, today + timedelta(days=1)]

    if source_id != 4:
        base_query += " AND SourceID = ?"
        params.append(source_id)

    base_query += " GROUP BY CAST(EventTime AS DATE)"

    cursor.execute(base_query, tuple(params))
    rows = cursor.fetchall()

    counts = {row[0].isoformat(): row[1] for row in rows}
    return {
        "today": counts.get(today.isoformat(), 0),
        "yesterday": counts.get(yesterday.isoformat(), 0),
    }
