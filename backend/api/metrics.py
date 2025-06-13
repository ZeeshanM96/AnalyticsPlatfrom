# backend/api/metrics.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from collections import defaultdict
from ..auth import decode_jwt_token, validate_date_range
from ..db import get_connection

router = APIRouter()
security = HTTPBearer()


@router.get("/getsourcemetrics/")
def get_source_metric_summary(
    from_date: str = Query(...),
    to_date: str = Query(...),
    sources: List[str] = Query(...),
    event_type: List[str] = Query(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
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

    placeholders_src = ",".join("?" for _ in sources)
    cursor.execute(
        f"SELECT SourceID, SourceName FROM Sources WHERE SourceName IN ({placeholders_src})", sources
    )
    id_lookup = cursor.fetchall()

    source_map = {name: sid for sid, name in id_lookup}
    missing_sources = [s for s in sources if s not in source_map]
    if missing_sources:
        raise HTTPException(status_code=400, detail=f"Invalid source(s): {missing_sources}")

    source_ids = list(source_map.values())

    placeholders_met = ",".join("?" for _ in event_type)
    placeholders_srcid = ",".join("?" for _ in source_ids)

    query = f"""
        SELECT SourceID, EventType, Count(EventType) as Total
        FROM Events
        WHERE EventTime >= ? AND EventTime <= ?
        AND SourceID IN ({placeholders_srcid})
        AND EventType IN ({placeholders_met})
        GROUP BY SourceID, EventType
    """

    params = [from_date, to_date] + source_ids + event_type
    cursor.execute(query, params)
    rows = cursor.fetchall()

    id_to_name = {v: k for k, v in source_map.items()}

    grouped = {}
    for source_id, metric, total in rows:
        source_name = id_to_name.get(source_id, f"Unknown-{source_id}")
        if metric not in grouped:
            grouped[metric] = {}
        grouped[metric][source_name] = total

    all_sources = sorted(set(s for g in grouped.values() for s in g.keys()))

    datasets = []
    for metric, src_data in grouped.items():
        datasets.append({
            "label": metric,
            "data": [src_data.get(s, 0) for s in all_sources]
        })

    return {
        "labels": all_sources,
        "datasets": datasets
    }


@router.get("/getmetricbytypes")
def get_metric_types(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT MetricType FROM AggregatedMetrics ORDER BY MetricType")
    rows = cursor.fetchall()

    return {"metrics": [row[0] for row in rows]}
