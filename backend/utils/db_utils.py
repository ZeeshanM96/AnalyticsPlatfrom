# This file contains utility functions for database operations related to alerts and user sources.

from fastapi import HTTPException
from datetime import date, datetime
from typing import Optional
from backend.utils.constants import ADMIN_SOURCE_ID
from backend.utils.dataclass_utils import AlertSummaryFilter, AlertResolutionFilter
from backend.utils.auth_utils import encrypt_key, decrypt_key


def get_source_id_by_user(cursor, user_id: int) -> int:
    cursor.execute("SELECT SourceID FROM Users WHERE UserID = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="User source not found")
    return row[0]


def credentials_exist(cursor, source_id: int, created_by: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) FROM ApiCredentials
        WHERE SourceId = ? AND CreatedBy = ?
    """,
        (source_id, created_by),
    )
    return cursor.fetchone()[0] > 0


def insert_api_credential(
    cursor, api_key: str, secret_key: str, source_id: int, created_by: str
) -> None:
    cursor.execute(
        """
        INSERT INTO ApiCredentials (
            ApiKey, SecretKey, SourceId, CreatedBy, DateCreated, DateUpdated
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            encrypt_key(api_key),
            encrypt_key(secret_key),
            source_id,
            created_by,
            datetime.now(),
            datetime.now(),
        ),
    )


def update_api_credential(
    cursor, api_key: str, secret_key: str, source_id: int, created_by: str
) -> None:
    cursor.execute(
        """
        UPDATE ApiCredentials
        SET ApiKey = ?, SecretKey = ?, DateUpdated = ?
        WHERE SourceId = ? AND CreatedBy = ?
    """,
        (
            encrypt_key(api_key),
            encrypt_key(secret_key),
            datetime.now(),
            source_id,
            created_by,
        ),
    )


def get_api_credentials(
    cursor, source_id: int, created_by: Optional[str] = None
) -> dict:
    if created_by is not None:
        cursor.execute(
            """
            SELECT ApiKey, SecretKey FROM ApiCredentials
            WHERE SourceId = ? AND CreatedBy = ?
            """,
            (source_id, created_by),
        )
    else:
        cursor.execute(
            """
            SELECT ApiKey, SecretKey FROM ApiCredentials
            WHERE SourceId = ? AND CreatedBy IS NULL
            """,
            (source_id,),
        )

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No credentials found")

    api_key = decrypt_key(row[0])
    secret_key = decrypt_key(row[1])

    return {"api_key": api_key, "secret_key": secret_key}


def get_all_keys(cursor) -> list[dict]:
    cursor.execute("SELECT SourceId, ApiKey, SecretKey FROM ApiCredentials")
    keys = []
    for row in cursor.fetchall():
        source_id = row[0]
        try:
            api_key = decrypt_key(row[1])
            secret_key = decrypt_key(row[2])
            keys.append(
                {"source_id": source_id, "api_key": api_key, "secret_key": secret_key}
            )
        except Exception as e:
            print(
                f"Warning: Failed to decrypt credentials for source_id {source_id}: {e}"
            )
            continue
    return keys


def get_all_sources(cursor) -> list[str]:
    cursor.execute("SELECT SourceName FROM Sources ORDER BY SourceName")
    return [row[0] for row in cursor.fetchall()]


def get_alert_counts_by_date(cursor, source_id: int, start: date, end: date) -> dict:
    query = """SELECT CAST(TriggeredAt AS DATE), COUNT(*) FROM Alerts
               WHERE Severity = 'Critical' AND TriggeredAt >= ? AND TriggeredAt < ?"""
    params = [start, end]
    if source_id != ADMIN_SOURCE_ID:
        query += " AND SourceID = ?"
        params.append(source_id)
    query += " GROUP BY CAST(TriggeredAt AS DATE)"

    cursor.execute(query, tuple(params))
    return {row[0].isoformat(): row[1] for row in cursor.fetchall()}


def get_distinct_alert_types(cursor, source_id: int, is_admin: bool) -> list[str]:
    if is_admin:
        cursor.execute("SELECT DISTINCT AlertType FROM Alerts")
    else:
        cursor.execute(
            "SELECT DISTINCT AlertType FROM Alerts WHERE SourceID = ?", (source_id,)
        )
    return [row[0] for row in cursor.fetchall()]


def get_distinct_severities(cursor, source_id: int, is_admin: bool) -> list[str]:
    if is_admin:
        cursor.execute("SELECT DISTINCT Severity FROM Alerts ORDER BY Severity")
    else:
        cursor.execute(
            "SELECT DISTINCT Severity FROM Alerts WHERE SourceID = ? ORDER BY Severity",
            (source_id,),
        )
    return [row[0] for row in cursor.fetchall()]


def get_distinct_batches(cursor, source_id: int, is_admin: bool) -> list[str]:
    if is_admin:
        cursor.execute(
            "SELECT DISTINCT BatchID FROM Batches WHERE BatchID IS NOT NULL ORDER BY BatchID"
        )
    else:
        cursor.execute(
            (
                "SELECT DISTINCT BatchID FROM Batches "
                "WHERE BatchID IS NOT NULL AND SourceID = ? "
                "ORDER BY BatchID"
            ),
            (source_id,),
        )
    return [row[0] for row in cursor.fetchall()]


def get_distinct_event_types(cursor, source_id: int, is_admin: bool) -> list[str]:
    if is_admin:
        cursor.execute("SELECT DISTINCT EventType FROM Events")
    else:
        cursor.execute(
            "SELECT DISTINCT EventType FROM Events WHERE SourceID = ?", (source_id,)
        )
    return [row[0] for row in cursor.fetchall()]


def get_all_metric_types(cursor) -> list[str]:
    cursor.execute(
        "SELECT DISTINCT MetricType FROM AggregatedMetrics ORDER BY MetricType"
    )
    return [row[0] for row in cursor.fetchall()]


def get_user_by_email(cursor, email: str):
    cursor.execute(
        "SELECT UserID, Email, HashedPassword FROM Users WHERE Email = ?", (email,)
    )
    return cursor.fetchone()


def email_exists(cursor, email: str) -> bool:
    cursor.execute("SELECT 1 FROM Users WHERE Email = ?", (email,))
    return cursor.fetchone() is not None


def insert_user(cursor, email: str, role: str, source_id: int, hashed_pw: bytes):
    cursor.execute(
        """
        INSERT INTO Users (Email, Role, CreatedAt, SourceID, HashedPassword)
        VALUES (?, ?, SYSDATETIME(), ?, ?)
        """,
        (email, role, source_id, hashed_pw),
    )


def get_user_details(cursor, user_id: int):
    cursor.execute(
        "SELECT Email, Role, SourceID FROM Users WHERE UserID = ?", (user_id,)
    )
    return cursor.fetchone()


def get_source_id_by_name(cursor, source_name: str):
    cursor.execute("SELECT SourceID FROM Sources WHERE SourceName = ?", (source_name,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_source_name_by_id(cursor, source_id: int):
    cursor.execute("SELECT SourceName FROM Sources WHERE SourceID = ?", (source_id,))
    row = cursor.fetchone()
    return row[0] if row else "Unknown"


def count_all_services(cursor):
    cursor.execute("SELECT COUNT(*) FROM Services")
    return cursor.fetchone()[0]


def count_running_services(cursor):
    cursor.execute("SELECT COUNT(*) FROM Services WHERE IsRunning = 1")
    return cursor.fetchone()[0]


def get_all_service_names(cursor):
    cursor.execute("SELECT DISTINCT ServiceName FROM Services ORDER BY ServiceName")
    return [row[0] for row in cursor.fetchall()]


def get_preferences_by_source(cursor, source_id: int) -> list[dict]:
    cursor.execute(
        """
        SELECT ViewName, PreferredView, Enabled
        FROM UserPreferences
        WHERE SourceID = ?
        ORDER BY ViewName
        """,
        (source_id,),
    )
    return [
        {"viewName": row[0], "preferredView": row[1], "enabled": bool(row[2])}
        for row in cursor.fetchall()
    ]


def update_preferences_by_source(cursor, source_id: int, preferences: list):
    for pref in preferences:
        cursor.execute(
            """
            UPDATE UserPreferences
            SET PreferredView = ?, Enabled = ?
            WHERE SourceID = ? AND ViewName = ?
            """,
            (pref.preferredView, int(pref.enabled), source_id, pref.viewName),
        )


def fetch_alert_summary(cursor, filter: AlertSummaryFilter):
    query = """
        SELECT
            BatchID,
            Severity,
            COUNT(*) as count
        FROM Alerts
        WHERE TriggeredAt BETWEEN ? AND ?
    """
    params = [filter.from_date, filter.to_date]

    if not filter.is_admin:
        query += " AND SourceID = ?"
        params.append(filter.source_id)

    if filter.batch_ids:
        placeholders = ", ".join("?" for _ in filter.batch_ids)
        query += f" AND BatchID IN ({placeholders})"
        params.extend(filter.batch_ids)

    if filter.severities:
        placeholders = ", ".join("?" for _ in filter.severities)
        query += f" AND Severity IN ({placeholders})"
        params.extend(filter.severities)

    query += " GROUP BY BatchID, Severity ORDER BY BatchID"
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def fetch_event_summary(cursor, filter: AlertResolutionFilter):
    placeholders = ", ".join("?" for _ in filter.event_types)
    params = [filter.from_date, filter.to_date] + filter.event_types

    if filter.is_admin:
        source_clause = "1=1"
    else:
        source_clause = "SourceID = ?"
        params = [filter.source_id] + params

    cursor.execute(
        f"""
        SELECT
            CONVERT(date, EventTime) AS EventDate,
            EventType,
            COUNT(*) AS Count
        FROM Events
        WHERE {source_clause}
          AND EventTime BETWEEN ? AND ?
          AND EventType IN ({placeholders})
        GROUP BY CONVERT(date, EventTime), EventType
        ORDER BY EventDate, EventType
        """,
        tuple(params),
    )

    return cursor.fetchall()


def get_source_ids_by_names(cursor, source_names: list[str]) -> dict[str, int]:
    placeholders = ", ".join("?" for _ in source_names)
    cursor.execute(
        f"SELECT SourceID, SourceName FROM Sources WHERE SourceName IN ({placeholders})",
        source_names,
    )
    return {name: sid for sid, name in cursor.fetchall()}


def fetch_source_event_metrics(
    cursor, from_date: str, to_date: str, source_ids: list[int], event_types: list[str]
):
    placeholders_srcid = ",".join("?" for _ in source_ids)
    placeholders_evt = ",".join("?" for _ in event_types)

    query = f"""
        SELECT SourceID, EventType, COUNT(EventType) as Total
        FROM Events
        WHERE EventTime >= ? AND EventTime <= ?
          AND SourceID IN ({placeholders_srcid})
          AND EventType IN ({placeholders_evt})
        GROUP BY SourceID, EventType
    """

    params = [from_date, to_date] + source_ids + event_types
    cursor.execute(query, params)
    return cursor.fetchall()


def fetch_service_metrics(
    cursor,
    from_date: str,
    to_date: str,
    service_names: list[str],
    metric_types: list[str],
):
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
    return cursor.fetchall()


def fetch_batch_event_counts(
    cursor, source_id: int, start_date, end_date, is_admin: bool
):
    query = """
        SELECT
            CAST(EventTime AS DATE) as event_date,
            COUNT(DISTINCT BatchID)
        FROM Events
        WHERE BatchID IS NOT NULL
          AND EventTime >= ? AND EventTime < ?
    """
    params = [start_date, end_date]

    if not is_admin:
        query += " AND SourceID = ?"
        params.append(source_id)

    query += " GROUP BY CAST(EventTime AS DATE)"
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def fetch_alert_resolution_summary(
    cursor, from_date, to_date, user_source_id, source_names, severity_list, is_admin
):
    filters = ["TriggeredAt BETWEEN ? AND ?"]
    params = [from_date, to_date]

    if source_names:
        placeholders = ",".join("?" for _ in source_names)
        filters.append(
            (
                f"a.SourceID IN (SELECT s2.SourceID FROM Sources s2 "
                f"WHERE s2.SourceName IN ({placeholders}))"
            )
        )
        params.extend(source_names)
    elif not is_admin:
        filters.append("a.SourceID = ?")
        params.append(user_source_id)

    if severity_list:
        placeholders = ",".join("?" for _ in severity_list)
        filters.append(f"a.Severity IN ({placeholders})")
        params.extend(severity_list)

    where_clause = " AND ".join(filters)

    query = f"""
        SELECT s.SourceName, a.Severity,
               CASE WHEN a.ResolvedAt IS NULL THEN 'Unresolved' ELSE 'Resolved' END AS Status,
               COUNT(*) as Count
        FROM Alerts a
        JOIN Sources s ON a.SourceID = s.SourceID
        WHERE {where_clause}
        GROUP BY s.SourceName, a.Severity,
                 CASE WHEN a.ResolvedAt IS NULL THEN 'Unresolved' ELSE 'Resolved' END
        ORDER BY s.SourceName, a.Severity
    """

    cursor.execute(query, params)
    return cursor.fetchall()
