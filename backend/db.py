# Backend/db.py
import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=ZEESHANMAJEED\MSSQLSERVER01;"
        "DATABASE=AWS;"
        "Trusted_Connection=yes;"
    )
    return conn
