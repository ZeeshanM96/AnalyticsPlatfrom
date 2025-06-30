# backend/api/preferences.py

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from backend.utils.auth_utils import decode_jwt_token
from backend.utils.db_conn import get_connection
from backend.utils.schemas_utils import PreferenceUpdate
from ..utils.db_utils import (
    get_source_id_by_user,
    get_preferences_by_source,
    update_preferences_by_source,
)
from ..utils.services_utils import validate_preferences

router = APIRouter()
security = HTTPBearer()


@router.get("/getuserpreferences")
def get_user_preferences(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()
    source_id = get_source_id_by_user(cursor, payload["user_id"])
    preferences = get_preferences_by_source(cursor, source_id)

    return {"sourceId": source_id, "preferences": preferences}


@router.post("/updatepreferences")
def update_user_preferences(
    preferences: List[PreferenceUpdate] = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    validate_preferences(preferences)

    conn = get_connection()
    cursor = conn.cursor()
    source_id = get_source_id_by_user(cursor, payload["user_id"])

    update_preferences_by_source(cursor, source_id, preferences)
    conn.commit()

    return {"success": True, "message": "Preferences updated successfully"}
