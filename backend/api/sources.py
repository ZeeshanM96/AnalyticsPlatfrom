# backend/api/sources.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.utils.auth_utils import (
    decode_jwt_token,
    is_admin,
    validate_date_range,
    parse_comma_separated,
)
from backend.utils.db_conn import get_connection
from ..utils.db_utils import (
    get_all_sources,
    get_source_id_by_user,
    fetch_alert_resolution_summary,
    get_source_name_by_id,
)
from ..utils.services_utils import build_resolution_summary_dataset

router = APIRouter()
security = HTTPBearer()


@router.get("/getsources")
def get_sources():
    conn = get_connection()
    cursor = conn.cursor()
    return {"sources": get_all_sources(cursor)}


@router.get("/getsourcesbyid")
def get_sources_by_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        source_id = get_source_id_by_user(cursor, payload["user_id"])
        admin = is_admin(source_id)

        if admin:
            sources = get_all_sources(cursor)
        else:
            source_name = get_source_name_by_id(cursor, source_id)
            sources = [source_name]

        return {"sources": sources}
    finally:
        conn.close()


@router.get("/getalertsbysource")
def get_resolution_summary(
    from_date: str,
    to_date: str,
    sources: str = "",
    severities: str = "",
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    validate_date_range(from_date, to_date)

    try:
        payload = decode_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = get_connection()
        cursor = conn.cursor()

        user_source_id = get_source_id_by_user(cursor, payload["user_id"])
        admin = is_admin(user_source_id)

        source_list = parse_comma_separated(sources)
        severity_list = parse_comma_separated(severities)

        rows = fetch_alert_resolution_summary(
            cursor,
            from_date,
            to_date,
            user_source_id,
            source_list,
            severity_list,
            admin,
        )

        return build_resolution_summary_dataset(rows)

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
