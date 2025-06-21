# backend/api/auth.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..db import get_connection
from ..auth import verify_password, create_jwt_token, hash_password, decode_jwt_token
from ..schemas import SignupRequest
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()
VALID_ROLES = ["Client", "Developer"]


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT UserID, Email, HashedPassword
        FROM Users
        WHERE Email = ?
    """,
        req.email,
    )

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, email, hashed_password_db = row

    if not isinstance(hashed_password_db, bytes):
        raise HTTPException(
            status_code=500,
            detail="Database error: Hashed password is not in expected format",
        )

    if not verify_password(req.password, bytes(hashed_password_db)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(user_id, email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/signup", status_code=201)
def signup(req: SignupRequest):
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role selected")

    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM Users WHERE Email = ?", (req.email,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    if req.role == "Client" and req.source == "AWS":
        raise HTTPException(
            status_code=400, detail="Clients cannot choose 'AWS' as a source"
        )

    if not req.source:
        raise HTTPException(status_code=400, detail="Source is required")

    cursor.execute("SELECT SourceID FROM Sources WHERE SourceName = ?", req.source)
    source_row = cursor.fetchone()
    if not source_row:
        raise HTTPException(status_code=400, detail="Invalid source selected")

    source_id = source_row[0]
    hashed_pw = hash_password(req.password)

    cursor.execute(
        """
        INSERT INTO Users (Email, Role, CreatedAt, SourceID, HashedPassword)
        VALUES (?, ?, SYSDATETIME(), ?, ?)
    """,
        req.email,
        req.role,
        source_id,
        hashed_pw,
    )

    conn.commit()
    return {"message": "User registered successfully"}


@router.get("/getuserdetails")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT Email, Role, SourceID FROM Users WHERE UserID = ?
    """,
        payload["user_id"],
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    email, role, source_id = row

    cursor.execute("SELECT SourceName FROM Sources WHERE SourceID = ?", source_id)
    source_row = cursor.fetchone()
    source_name = source_row[0] if source_row else "Unknown"

    return {"email": email, "role": role, "source": source_name}
