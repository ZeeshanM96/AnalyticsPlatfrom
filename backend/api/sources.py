# backend/api/sources.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..auth import decode_jwt_token, is_admin, validate_date_range
from ..db import get_connection
from collections import defaultdict

router = APIRouter()
security = HTTPBearer()


@router.get("/getsources")
def get_sources():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SourceName FROM Sources ORDER BY SourceName")
    return {"sources": [row[0] for row in cursor.fetchall()]}


@router.get("/getsourcesbyid")
def get_sources_by_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["user_id"]
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch the user's SourceID
    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")

    source_id = row[0]

    # Return sources based on SourceID (admin or not)
    if is_admin(source_id):
        cursor.execute("SELECT SourceName FROM Sources ORDER BY SourceName")
    else:
        cursor.execute(
            "SELECT SourceName FROM Sources WHERE SourceID = ?", (source_id,)
        )

    return {"sources": [row[0] for row in cursor.fetchall()]}


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

        cursor.execute(
            "SELECT SourceID FROM Users WHERE UserID = ?", (payload["user_id"],)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=403, detail="User source not found")

        user_source_id = row[0]

        source_list = [s.strip() for s in sources.split(",") if s.strip()]
        severity_list = [s.strip() for s in severities.split(",") if s.strip()]

        filters = ["TriggeredAt BETWEEN ? AND ?"]
        params = [from_date, to_date]

        if source_list:
            placeholders = ",".join("?" * len(source_list))
            filters.append(
                (
                    "a.SourceID IN (SELECT s2.SourceID FROM Sources s2 "
                    f"WHERE s2.SourceName IN ({placeholders}))"
                )
            )
            params.extend(source_list)
        elif user_source_id != 4:
            filters.append("a.SourceID = ?")
            params.append(user_source_id)

        if severity_list:
            placeholders = ",".join("?" * len(severity_list))
            filters.append(f"a.Severity IN ({placeholders})")
            params.extend(severity_list)

        where_clause = " AND ".join(filters)

        query = (
            "SELECT "
            "s.SourceName, "
            "a.Severity, "
            "CASE WHEN a.ResolvedAt IS NULL THEN 'Unresolved' ELSE 'Resolved' END AS Status, "
            "COUNT(*) as Count "
            "FROM Alerts a "
            "JOIN Sources s ON a.SourceID = s.SourceID "
            f"WHERE {where_clause} "
            "GROUP BY s.SourceName, a.Severity, "
            "CASE WHEN a.ResolvedAt IS NULL THEN 'Unresolved' ELSE 'Resolved' END "
            "ORDER BY s.SourceName, a.Severity"
        )

        cursor.execute(query, params)
        rows = cursor.fetchall()

        severity_levels = ["Critical", "Info", "Warning"]
        resolved_map = defaultdict(lambda: defaultdict(int))
        unresolved_map = defaultdict(lambda: defaultdict(int))
        sources_set = set()

        for source, severity, status, count in rows:
            sources_set.add(source)
            if status == "Resolved":
                resolved_map[severity][source] += count
            else:
                unresolved_map[severity][source] += count

        sorted_sources = sorted(sources_set)
        labels = sorted_sources

        def get_data(map_, severity):
            return [map_[severity].get(source, 0) for source in labels]

        datasets = []
        color_map = {
            "Critical-Resolved": "#5cb85c",
            "Critical-Unresolved": "#d9534f",
            "Info-Resolved": "#5bc0de",
            "Info-Unresolved": "#dff0d8",
            "Warning-Resolved": "#f7ecb5",
            "Warning-Unresolved": "#f0ad4e",
        }

        for severity in severity_levels:
            datasets.append(
                {
                    "label": f"{severity} - Resolved",
                    "backgroundColor": color_map.get(f"{severity}-Resolved", "#ccc"),
                    "data": get_data(resolved_map, severity),
                    "stack": severity,
                }
            )
            datasets.append(
                {
                    "label": f"{severity} - Unresolved",
                    "backgroundColor": color_map.get(f"{severity}-Unresolved", "#ccc"),
                    "data": get_data(unresolved_map, severity),
                    "stack": severity,
                }
            )

        return {"labels": labels, "datasets": datasets}

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
