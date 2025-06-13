# Backend/db.py
import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=your_server_name;"
        "DATABASE=AWS;"
        "Trusted_Connection=yes;"
    )
    return conn
