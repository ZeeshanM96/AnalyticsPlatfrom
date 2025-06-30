# backend/api/services.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.utils.auth_utils import (
    decode_jwt_token,
    parse_comma_separated,
    validate_date_range,
)
from backend.utils.db_conn import get_connection
from ..utils.db_utils import (
    count_all_services,
    count_running_services,
    get_all_service_names,
    fetch_service_metrics,
)
from ..utils.services_utils import build_service_metric_dataset

router = APIRouter()
security = HTTPBearer()


@router.get("/getservicestatus")
def get_services_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        return {
            "total": count_all_services(cursor),
            "running": count_running_services(cursor),
        }
    finally:
        conn.close()


@router.get("/getservices")
def get_service_names(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    cursor = conn.cursor()
    return {"services": get_all_service_names(cursor)}


@router.get("/getservicemetrics")
def get_service_metrics_api(
    from_date: str,
    to_date: str,
    services: str = "",
    metrics: str = "",
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    validate_date_range(from_date, to_date)

    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_connection()
    try:
        cursor = conn.cursor()

        service_names = parse_comma_separated(services)
        metric_types = parse_comma_separated(metrics)

        rows = fetch_service_metrics(
            cursor, from_date, to_date, service_names, metric_types
        )
        return build_service_metric_dataset(rows)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    finally:
        conn.close()
