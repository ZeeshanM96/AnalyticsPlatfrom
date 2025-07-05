import os
from dotenv import load_dotenv

# Load test environment variables early if running tests
if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in os.getenv("_", ""):
    load_dotenv(dotenv_path=".env.local")
else:
    load_dotenv(dotenv_path=".env")
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.websocket import websocket
from backend.api.oauth import router as oauth_router
from injestion.external_ingest import router as ingest_router
from injestion.set_api_key import prewarm_api_credentials
from starlette.middleware.sessions import SessionMiddleware
import os
import asyncio
import logging
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


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, prewarm_api_credentials)
        logger.info("✅ API credentials prewarmed successfully")
    except Exception as e:
        logger.critical(f"❌ Failed to prewarm API credentials: {e}")
        raise
    yield


app = FastAPI(lifespan=lifespan)

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
app.include_router(oauth_router)
app.include_router(ingest_router)
app.include_router(apikey.router)
