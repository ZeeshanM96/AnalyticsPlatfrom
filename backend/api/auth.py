# backend/api/auth.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.utils.db_conn import get_connection
from backend.utils.auth_utils import (
    verify_password,
    create_jwt_token,
    hash_password,
    decode_jwt_token,
)
from ..utils.db_utils import (
    get_user_by_email,
    email_exists,
    insert_user,
    get_user_details,
    get_source_id_by_name,
    get_source_name_by_id,
)
from backend.utils.schemas_utils import SignupRequest, LoginRequest
from ..utils.services_utils import validate_signup_data

router = APIRouter()
security = HTTPBearer()


@router.post("/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()

    row = get_user_by_email(cursor, req.email)
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, email, hashed_password_db = row

    if not isinstance(hashed_password_db, bytes):
        raise HTTPException(status_code=500, detail="Password format error")

    if not verify_password(req.password, bytes(hashed_password_db)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(user_id, email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/signup", status_code=201)
def signup(req: SignupRequest):
    validate_signup_data(req)

    conn = get_connection()
    cursor = conn.cursor()

    if email_exists(cursor, req.email):
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    source_id = get_source_id_by_name(cursor, req.source)
    if not source_id:
        raise HTTPException(status_code=400, detail="Invalid source selected")

    hashed_pw = hash_password(req.password)
    insert_user(cursor, req.email, req.role, source_id, hashed_pw)

    conn.commit()
    return {"message": "User registered successfully"}


@router.get("/getuserdetails")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()

    row = get_user_details(cursor, payload["user_id"])
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    email, role, source_id = row
    source_name = get_source_name_by_id(cursor, source_id)

    return {"email": email, "role": role, "source": source_name}
