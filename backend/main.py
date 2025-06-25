from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.kafka import websocket

from backend.api import (
    auth,
    sources,
    events,
    alerts,
    services,
    preferences,
    metrics,
    frontend,
)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
