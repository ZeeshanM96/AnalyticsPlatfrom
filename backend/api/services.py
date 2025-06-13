# backend/api/services.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..auth import decode_jwt_token, validate_date_range
from ..db import get_connection
from typing import List
from collections import defaultdict

router = APIRouter()
security = HTTPBearer()


@router.get("/getservicestatus")
def get_services_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Services")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Services WHERE IsRunning = 1")
    running = cursor.fetchone()[0]

    return {
        "total": total,
        "running": running
    }


@router.get("/getservices")
def get_service_names(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT ServiceName FROM Services ORDER BY ServiceName")
    rows = cursor.fetchall()

    return {"services": [row[0] for row in rows]}


@router.get("/getservicemetrics")
def get_service_metrics(
    from_date: str,
    to_date: str,
    services: str = "",
    metrics: str = "",
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    validate_date_range(from_date, to_date)
    try:
        payload = decode_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = get_connection()
        cursor = conn.cursor()

        service_names = [s.strip() for s in services.split(",") if s.strip()]
        metric_types = [m.strip() for m in metrics.split(",") if m.strip()]

        filters = ["am.WindowStart BETWEEN ? AND ?"]
        params = [from_date, to_date]

        if service_names:
            placeholders = ", ".join("?" for _ in service_names)
            filters.append(f"s.ServiceName IN ({placeholders})")
            params.extend(service_names)

        if metric_types:
            placeholders = ", ".join("?" for _ in metric_types)
            filters.append(f"am.MetricType IN ({placeholders})")
            params.extend(metric_types)

        where_clause = " AND ".join(filters)

        query = f"""
            SELECT 
                CONVERT(DATE, am.WindowStart) AS Day,
                s.ServiceName,
                am.MetricType,
                AVG(am.MetricValue) AS AvgValue
            FROM AggregatedMetrics am
            JOIN Services s ON am.ServiceID = s.ServiceID
            WHERE {where_clause}
            GROUP BY CONVERT(DATE, am.WindowStart), s.ServiceName, am.MetricType
            ORDER BY Day
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        all_dates = set()
        grouped = defaultdict(lambda: defaultdict(float))  # {label: {date: value}}

        for day, service_name, metric_type, value in rows:
            label = f"{service_name} - {metric_type}"
            date_str = day.strftime("%Y-%m-%d")
            grouped[label][date_str] = value
            all_dates.add(date_str)

        sorted_dates = sorted(all_dates)
        datasets = []

        for label, values in grouped.items():
            datasets.append({
                "label": label,
                "data": [values.get(date, 0) for date in sorted_dates],
                "fill": False,
                "borderWidth": 2
            })

        return {
            "labels": sorted_dates,
            "datasets": datasets
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
