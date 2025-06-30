# backend/api/metrics.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from backend.utils.auth_utils import decode_jwt_token, validate_date_range
from backend.utils.db_conn import get_connection
from backend.utils.db_utils import (
    get_source_ids_by_names,
    get_all_metric_types,
    fetch_source_event_metrics,
)
from backend.utils.services_utils import build_source_metric_datasets

router = APIRouter()
security = HTTPBearer()


@router.get("/getsourcemetrics/")
def get_source_metric_summary(
    from_date: str = Query(...),
    to_date: str = Query(...),
    sources: List[str] = Query(...),
    event_type: List[str] = Query(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    validate_date_range(from_date, to_date)

    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()

    # Validate and resolve source IDs
    source_map = get_source_ids_by_names(cursor, sources)
    missing_sources = [s for s in sources if s not in source_map]
    if missing_sources:
        raise HTTPException(
            status_code=400, detail=f"Invalid source(s): {missing_sources}"
        )

    source_ids = list(source_map.values())
    id_to_name = {v: k for k, v in source_map.items()}

    rows = fetch_source_event_metrics(
        cursor, from_date, to_date, source_ids, event_type
    )
    return build_source_metric_datasets(rows, id_to_name)


@router.get("/getmetricbytypes")
def get_metric_types(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()
    return {"metrics": get_all_metric_types(cursor)}
