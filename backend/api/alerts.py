# backend/api/alerts.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..auth import decode_jwt_token, is_admin, validate_date_range
from ..db import get_connection
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict

router = APIRouter()
security = HTTPBearer()


@router.get("/getalertstatus")
def get_critical_alerts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the count of critical alerts for today and yesterday.

    **Authorization:** Bearer token required.

    **Returns:**
        {
            "today": <int>,      # Number of critical alerts today
            "yesterday": <int>   # Number of critical alerts yesterday
        }
    """
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
            CAST(TriggeredAt AS DATE) as alert_date,
            COUNT(*)
        FROM Alerts
        WHERE Severity = 'Critical'
          AND TriggeredAt >= ? AND TriggeredAt < ?
    """
    params = [yesterday, today + timedelta(days=1)]

    if source_id != 4:
        base_query += " AND SourceID = ?"
        params.append(source_id)

    base_query += " GROUP BY CAST(TriggeredAt AS DATE)"

    cursor.execute(base_query, tuple(params))
    rows = cursor.fetchall()

    counts = {row[0].isoformat(): row[1] for row in rows}
    return {
        "today": counts.get(today.isoformat(), 0),
        "yesterday": counts.get(yesterday.isoformat(), 0)
    }


@router.get("/getalertsbybatch")
def get_alert_summary(
    from_date: str,
    to_date: str,
    batches: Optional[str] = "",
    severities: Optional[str] = "",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get a summary of alerts grouped by batch and severity for a given date range.

    **Parameters:**
        - from_date (str, required): Start date (YYYY-MM-DD)
        - to_date (str, required): End date (YYYY-MM-DD)
        - batches (str, optional): Comma-separated list of batch IDs to filter
        - severities (str, optional): Comma-separated list of severities to filter

    **Authorization:** Bearer token required.

    **Returns:**
        {
            "labels": [<batchId1>, <batchId2>, ...],
            "datasets": [
                {
                    "label": <severity>,
                    "data": [<count_for_batch1>, <count_for_batch2>, ...],
                    "borderWidth": 2,
                    "fill": False
                },
                ...
            ]
        }
    """
    validate_date_range(from_date, to_date)
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
    batch_list = [b.strip() for b in batches.split(",") if b.strip()]
    severity_list = [s.strip() for s in severities.split(",") if s.strip()]

    query = """
        SELECT 
            BatchID,
            Severity,
            COUNT(*) as count
        FROM Alerts
        WHERE TriggeredAt BETWEEN ? AND ?
    """
    params = [from_date, to_date]

    if source_id != 4:
        query += " AND SourceID = ?"
        params.append(source_id)

    if batch_list:
        placeholders = ", ".join("?" for _ in batch_list)
        query += f" AND BatchID IN ({placeholders})"
        params.extend(batch_list)

    if severity_list:
        placeholders = ", ".join("?" for _ in severity_list)
        query += f" AND Severity IN ({placeholders})"
        params.extend(severity_list)

    query += " GROUP BY BatchID, Severity ORDER BY BatchID"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    result = defaultdict(lambda: defaultdict(int))
    batch_set = set()

    for batch_id, alert_type, count in rows:
        result[alert_type][batch_id] = count
        batch_set.add(batch_id)

    sorted_batches = sorted(batch_set)
    datasets = []
    for alert_type, batch_counts in result.items():
        datasets.append({
            "label": alert_type,
            "data": [batch_counts.get(bid, 0) for bid in sorted_batches],
            "borderWidth": 2,
            "fill": False
        })

    return {
        "labels": sorted_batches,
        "datasets": datasets
    }


@router.get("/getalertbytypes")
def get_alert_types(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get a list of all alert types available to the user.

    **Authorization:** Bearer token required.

    **Returns:**
        {
            "alertTypes": [<type1>, <type2>, ...]
        }
    """
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (payload["user_id"],))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")

    source_id = row[0]

    if is_admin(source_id):
        cursor.execute("SELECT DISTINCT AlertType FROM Alerts")
    else:
        cursor.execute("SELECT DISTINCT AlertType FROM Alerts WHERE SourceID = ?", (source_id,))

    return {"alertTypes": [row[0] for row in cursor.fetchall()]}


@router.get("/getbatches")
def get_alert_batches(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get a list of all batch IDs available to the user.

    **Authorization:** Bearer token required.

    **Returns:**
        {
            "batchIds": [<batchId1>, <batchId2>, ...]
        }
    """
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
        cursor.execute("""
            SELECT DISTINCT BatchID 
            FROM Batches 
            WHERE BatchID IS NOT NULL 
            ORDER BY BatchID
        """)
    else:
        cursor.execute("""
            SELECT DISTINCT BatchID 
            FROM Batches 
            WHERE BatchID IS NOT NULL AND SourceID = ? 
            ORDER BY BatchID
        """, (source_id,))

    return {"batchIds": [row[0] for row in cursor.fetchall()]}


@router.get("/getseveritiesbytypes")
def get_alert_severities(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get a list of all alert severities available to the user.

    **Authorization:** Bearer token required.

    **Returns:**
        {
            "severities": [<severity1>, <severity2>, ...]
        }
    """
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (payload["user_id"],))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")

    source_id = row[0]

    if is_admin(source_id):
        cursor.execute("SELECT DISTINCT Severity FROM Alerts ORDER BY Severity")
    else:
        cursor.execute("SELECT DISTINCT Severity FROM Alerts WHERE SourceID = ? ORDER BY Severity", (source_id,))

    return {"severities": [row[0] for row in cursor.fetchall()]}
