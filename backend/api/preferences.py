# backend/api/preferences.py

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from ..auth import decode_jwt_token
from ..db import get_connection

router = APIRouter()
security = HTTPBearer()


class PreferenceUpdate(BaseModel):
    viewName: str
    preferredView: str
    enabled: bool


@router.get("/getuserpreferences")
def get_user_preferences(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    source_id = row[0]

    cursor.execute("""
        SELECT ViewName, PreferredView, Enabled
        FROM UserPreferences
        WHERE SourceID = ?
        ORDER BY ViewName
    """, (source_id,))

    preferences = [
        {
            "viewName": row[0],
            "preferredView": row[1],
            "enabled": bool(row[2])
        }
        for row in cursor.fetchall()
    ]

    return {"sourceId": source_id, "preferences": preferences}


@router.post("/updatepreferences")
def update_user_preferences(
    preferences: List[PreferenceUpdate] = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    source_id = row[0]

    for pref in preferences:
        cursor.execute("""
            UPDATE UserPreferences
            SET PreferredView = ?, Enabled = ?
            WHERE SourceID = ? AND ViewName = ?
        """, (pref.preferredView, int(pref.enabled), source_id, pref.viewName))

    conn.commit()
    return {"success": True, "message": "Preferences updated successfully"}
