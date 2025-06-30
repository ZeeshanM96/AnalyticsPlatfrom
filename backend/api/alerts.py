# backend/api/alerts.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.utils.auth_utils import (
    decode_jwt_token,
    is_admin,
    validate_date_range,
    parse_comma_separated,
)

from backend.utils.db_conn import get_connection
from datetime import date, timedelta
from typing import Optional
from backend.utils.db_utils import (
    get_source_id_by_user,
    get_alert_counts_by_date,
    fetch_alert_summary,
    get_distinct_alert_types,
    get_distinct_severities,
    get_distinct_batches,
)
from backend.utils.services_utils import build_alert_chart_dataset


router = APIRouter()
security = HTTPBearer()


@router.get("/getalertstatus")
def get_critical_alerts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()

    source_id = get_source_id_by_user(cursor, payload["user_id"])
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    counts = get_alert_counts_by_date(cursor, source_id, yesterday, tomorrow)

    return {
        "today": counts.get(today.isoformat(), 0),
        "yesterday": counts.get(yesterday.isoformat(), 0),
    }


@router.get("/getalertbytypes")
def get_alert_types(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()
    source_id = get_source_id_by_user(cursor, payload["user_id"])
    admin = is_admin(source_id)

    types = get_distinct_alert_types(cursor, source_id, admin)
    return {"alertTypes": types}


@router.get("/getbatches")
def get_alert_batches(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()
    source_id = get_source_id_by_user(cursor, payload["user_id"])
    admin = is_admin(source_id)

    batch_ids = get_distinct_batches(cursor, source_id, admin)
    return {"batchIds": batch_ids}


@router.get("/getseveritiesbytypes")
def get_alert_severities(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()
    source_id = get_source_id_by_user(cursor, payload["user_id"])
    admin = is_admin(source_id)

    severities = get_distinct_severities(cursor, source_id, admin)
    return {"severities": severities}


@router.get("/getalertsbybatch")
def get_alert_summary(
    from_date: str,
    to_date: str,
    batches: Optional[str] = "",
    severities: Optional[str] = "",
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    validate_date_range(from_date, to_date)

    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()

    user_id = payload["user_id"]
    source_id = get_source_id_by_user(cursor, user_id)
    admin = is_admin(source_id)

    batch_list = parse_comma_separated(batches)
    severity_list = parse_comma_separated(severities)

    rows = fetch_alert_summary(
        cursor,
        source_id,
        from_date,
        to_date,
        batch_list,
        severity_list,
        is_admin=admin,
    )

    return build_alert_chart_dataset(rows)
