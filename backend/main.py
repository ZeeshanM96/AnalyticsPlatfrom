from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.websocket import websocket
from backend.api.google_oauth import router as google_auth_router
from injestion.external_ingest import router as ingest_router
from starlette.middleware.sessions import SessionMiddleware
import os
from backend.api import (
    auth,
    sources,
    events,
    alerts,
    services,
    preferences,
    metrics,
    frontend,
    set_apikey as apikey,
)

app = FastAPI()

SESSION_SECRET = os.environ.get("SESSION_SECRET")
# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "super-secret-key"),
)

# Static files
app.mount("/static/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/static/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/html", StaticFiles(directory="frontend/html"), name="html")
app.mount("/static", StaticFiles(directory="frontend/images"), name="images")


# Include routers
app.include_router(frontend.router)
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(services.router)
app.include_router(preferences.router)
app.include_router(metrics.router)
app.include_router(websocket.router)
app.include_router(google_auth_router)
app.include_router(ingest_router)
app.include_router(apikey.router)
