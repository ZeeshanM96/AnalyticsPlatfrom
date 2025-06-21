# backend/api/frontend.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()


@router.get("/")
def serve_frontend():
    index_path = os.path.join("frontend", "html", "login.html")
    print("Serving index from:", os.path.abspath(index_path))

    if not os.path.exists(index_path):
        print("login.html NOT FOUND, please check the path.")
        raise HTTPException(status_code=404, detail="login.html missing")

    return FileResponse(index_path, media_type="text/html")


@router.get("/dashboard")
def serve_dashboard():
    dashboard_path = os.path.join("frontend", "html", "dashboard.html")
    return FileResponse(dashboard_path)
