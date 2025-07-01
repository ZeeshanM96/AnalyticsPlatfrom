from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.utils.auth_utils import decode_jwt_token, is_admin
from backend.utils.schemas_utils import CredentialRequest
from backend.utils.db_utils import (
    get_source_id_by_user,
    credentials_exist,
    insert_api_credential,
    update_api_credential,
)
from backend.utils.db_conn import get_connection

router = APIRouter()
security = HTTPBearer()


@router.post("/setApi")
def insert_api_credentials(
    body: CredentialRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = decode_jwt_token(credentials.credentials)

    if not payload or "user_id" not in payload or "email" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload["user_id"]
    user_email = payload["email"]

    conn = get_connection()
    try:
        cursor = conn.cursor()
        source_id = get_source_id_by_user(cursor, user_id)
        admin = is_admin(source_id)

        if credentials_exist(cursor, source_id, user_email):
            if admin:
                update_api_credential(
                    cursor, body.ApiKey, body.SecretKey, source_id, user_email
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Credentials already exist. Please delete or rotate first.",
                )
        else:
            insert_api_credential(
                cursor, body.ApiKey, body.SecretKey, source_id, user_email
            )

        conn.commit()
        return {"success": True}
    finally:
        conn.close()
