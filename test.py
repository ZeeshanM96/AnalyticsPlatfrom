from backend.utils.db_utils import get_api_credentials
from backend.utils.db_conn import get_connection



if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    creds = get_api_credentials(cursor, 3, "wardah@gmail.com")
    print(creds["api_key"], creds["secret_key"])
