from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from backend.utils.db_conn import get_connection
from backend.utils.auth_utils import create_jwt_token
import os

router = APIRouter()


oauth = OAuth()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/auth/google")
async def login_with_google(request: Request):
    redirect_uri = request.url_for("auth_google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    print("GOOGLE_CLIENT_ID:", os.environ.get("GOOGLE_CLIENT_ID"))
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        if not user_info or "email" not in user_info:
            raise HTTPException(
                status_code=400, detail="No email found in Google profile"
            )

    except Exception:
        raise HTTPException(status_code=400, detail="Google login failed")

    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email found in Google profile")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT UserID, Role, SourceID FROM Users WHERE Email = ?", (email,))
    row = cursor.fetchone()

    if row:
        user_id, role, source_id = row

        cursor.execute(
            "SELECT SourceName FROM Sources WHERE SourceID = ?", (source_id,)
        )

        token = create_jwt_token(user_id, email)

        return RedirectResponse(
            f"http://127.0.0.1:8000/dashboard?token={token}", status_code=303
        )

    return RedirectResponse(f"http://127.0.0.1:8000/html/login.html?email={email}")


@router.post("/auth/google/complete-signup")
async def complete_signup(request: Request):
    form = await request.form()
    email = form.get("email")
    role = form.get("role")
    source_name = form.get("source")

    if not email or not role or not source_name:
        raise HTTPException(status_code=400, detail="Missing required fields")

    conn = get_connection()
    cursor = conn.cursor()

    # Lookup SourceID
    cursor.execute("SELECT SourceID FROM Sources WHERE SourceName = ?", (source_name,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid source name")
    source_id = row[0]

    # Insert and retrieve UserID in one go
    cursor.execute(
        "INSERT INTO Users (Email, Role, SourceID) OUTPUT INSERTED.UserID VALUES (?, ?, ?)",
        (email, role, source_id),
    )
    user_id = cursor.fetchone()[0]
    conn.commit()

    token = create_jwt_token(user_id, email)

    return RedirectResponse(f"/dashboard?token={token}", status_code=303)
