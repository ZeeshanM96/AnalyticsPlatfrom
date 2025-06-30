# backend/api/events.py

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
from ..utils.db_utils import (
    get_source_id_by_user,
    get_distinct_event_types,
    fetch_event_summary,
    fetch_batch_event_counts,
)
from ..utils.dataclass_utils import AlertResolutionFilter
from ..utils.services_utils import build_event_dataset

router = APIRouter()
security = HTTPBearer()


@router.get("/geteventtypes")
def get_event_types(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        source_id = get_source_id_by_user(cursor, payload["user_id"])
        admin = is_admin(source_id)

        types = get_distinct_event_types(cursor, source_id, admin)
        return {"eventTypes": types}
    finally:
        conn.close()


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

    conn = get_connection()
    try:
        cursor = conn.cursor()
        source_id = get_source_id_by_user(cursor, payload["user_id"])
        admin = is_admin(source_id)

        event_list = parse_comma_separated(events)
        if not event_list:
            raise HTTPException(
                status_code=400, detail="At least one event type is required."
            )

        rows = fetch_event_summary(
            cursor,
            AlertResolutionFilter(
                source_id=source_id,
                from_date=from_date,
                to_date=to_date,
                event_types=event_list,
                is_admin=admin,
            ),
        )
        return build_event_dataset(rows)
    finally:
        conn.close()


@router.get("/getbatchstatus")
def get_batch_counts(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        source_id = get_source_id_by_user(cursor, payload["user_id"])
        admin = is_admin(source_id)

        today = date.today()
        yesterday = today - timedelta(days=1)
        end_date = today + timedelta(days=1)

        rows = fetch_batch_event_counts(cursor, source_id, yesterday, end_date, admin)
        counts = {row[0].isoformat(): row[1] for row in rows}

        return {
            "today": counts.get(today.isoformat(), 0),
            "yesterday": counts.get(yesterday.isoformat(), 0),
        }
    finally:
        conn.close()
