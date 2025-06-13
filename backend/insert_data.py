# insert_data.py
import pyodbc
import time
import random
from db import get_connection
from datetime import datetime

def insert_record():
    conn = get_connection()
    cursor = conn.cursor()

    while True:
        source_id = random.choice([1, 2, 3, 4])

        if source_id == 4:
            metric_name = "CPU_Usage"
            value = round(random.uniform(10.0, 95.0), 2)  
        else:
            metric_name = "BatchCount"
            value = random.randint(5, 100)  

        cursor.execute(
            "INSERT INTO RealTimeData (source_id, metric_name, value) VALUES (?, ?, ?)",
            source_id, metric_name, value
        )
        conn.commit()
        print(f"[{datetime.now()}] Inserted: Source {source_id}, {metric_name} = {value}")
        time.sleep(5)

if __name__ == "__main__":
    insert_record()
