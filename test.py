import os
import pyodbc
from fastapi import HTTPException
from dotenv import load_dotenv
from backend.utils.auth_utils import decrypt_key

load_dotenv()

def get_connection():
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
    )
    return conn

def get_api_credentials(cursor, source_id: int, created_by: str) -> dict:
    cursor.execute(
        """
        SELECT ApiKey, SecretKey FROM ApiCredentials
        WHERE SourceId = ? AND CreatedBy = ?
        """,
        (source_id, created_by),
    )

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No credentials found")

    api_key = decrypt_key(row[0])
    secret_key = decrypt_key(row[1])

    return {"api_key": api_key, "secret_key": secret_key}


# Main logic
if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    creds = get_api_credentials(cursor, 4, "zeeshanmajeedabdul@gmail.com")
    print(creds["api_key"], creds["secret_key"])
