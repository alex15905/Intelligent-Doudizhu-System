from fastapi import APIRouter
from app.config import HOST, PORT

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/info")
def app_info():
    return {
        "name": "DouDiZhuAI",
        "version": "1.0.0",
        "backend": "FastAPI",
        "host": HOST,
        "port": PORT,
    }
