from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from backend.utils.db_conn import get_connection
from fastapi.responses import JSONResponse
from backend.utils.auth_utils import create_jwt_token, clean_guest_email
import os
from typing import Literal
import secrets

router = APIRouter()


oauth = OAuth()

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
OUTLOOK_CLIENT_ID = os.environ.get("OUTLOOK_CLIENT_ID")
OUTLOOK_CLIENT_SECRET = os.environ.get("OUTLOOK_CLIENT_SECRET")
OUTLOOK_TENANT_ID = os.environ.get("OUTLOOK_TENANT_ID")
BASE_URL = os.environ.get("BASE_URL")

required_env_vars = {
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
    "GITHUB_CLIENT_ID": GITHUB_CLIENT_ID,
    "GITHUB_CLIENT_SECRET": GITHUB_CLIENT_SECRET,
    "OUTLOOK_CLIENT_ID": OUTLOOK_CLIENT_ID,
    "OUTLOOK_CLIENT_SECRET": OUTLOOK_CLIENT_SECRET,
    "OUTLOOK_TENANT_ID": OUTLOOK_TENANT_ID,
}

missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise RuntimeError(
        f"Missing required environment variables for OAuth: {', '.join(missing_vars)}"
    )

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

oauth.register(
    name="outlook",
    client_id=OUTLOOK_CLIENT_ID,
    client_secret=OUTLOOK_CLIENT_SECRET,
    server_metadata_url=(
        f"https://login.microsoftonline.com/"
        f"{OUTLOOK_TENANT_ID}/v2.0/.well-known/openid-configuration"
    ),
    api_base_url="https://graph.microsoft.com/v1.0/",
    client_kwargs={
        "scope": "openid email profile User.Read",
    },
)


@router.get("/auth/{provider}")
async def oauth_login(
    request: Request, provider: Literal["google", "github", "outlook"]
):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await oauth.create_client(provider).authorize_redirect(
        request, redirect_uri, state=state
    )


@router.get("/auth/{provider}/callback")
async def oauth_callback(
    request: Request, provider: Literal["google", "github", "outlook"]
):
    try:
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        if provider == "google":
            user_info = token.get("userinfo")
            if not user_info or "email" not in user_info:
                raise HTTPException(
                    status_code=400, detail="No email found in Google profile"
                )
            email = user_info["email"]

        elif provider == "github":
            user_data = await client.get("user", token=token)
            emails_data = await client.get("user/emails", token=token)

            user_info = user_data.json()
            emails_info = emails_data.json()

            email = next((e["email"] for e in emails_info if e.get("primary")), None)
            if not email:
                raise HTTPException(status_code=400, detail="Primary email not found")

        elif provider == "outlook":
            user_data = await client.get("me", token=token)
            user_info = user_data.json()

            raw_email = user_info.get("mail") or user_info.get("userPrincipalName")
            email = clean_guest_email(raw_email)

            if not email:
                raise HTTPException(
                    status_code=400, detail="Email not found in Outlook profile"
                )

        else:
            raise HTTPException(status_code=400, detail="Unsupported provider")

    except Exception as e:
        print("OAuth callback error:", str(e))
        return JSONResponse(
            status_code=400,
            content={"detail": f"{provider.capitalize()} login failed: {str(e)}"},
        )

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT UserID, Role, SourceID FROM Users WHERE Email = ?", (email,)
        )
        row = cursor.fetchone()

        if row:
            user_id = row[0]
            token = create_jwt_token(user_id, email)
            return RedirectResponse(
                f"{BASE_URL}/dashboard?token={token}", status_code=303
            )

        # If user doesn't exist, redirect to signup completion
        return RedirectResponse(
            f"{BASE_URL}/html/login.html?email={email}&provider={provider}"
        )
    finally:
        if conn:
            conn.close()


@router.post("/auth/oauth/complete-signup")
async def complete_signup(request: Request):
    form = await request.form()
    email = form.get("email")
    role = form.get("role")
    source_name = form.get("source")

    if not email or not role or not source_name:
        raise HTTPException(status_code=400, detail="Missing required fields")

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Lookup SourceID
        cursor.execute(
            "SELECT SourceID FROM Sources WHERE SourceName = ?", (source_name,)
        )
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
    finally:
        if conn:
            conn.close()
