from fastapi import APIRouter
from core.models.dto.monitoring.health import Health

health_router = APIRouter()

@health_router.get("/")
def health() -> Health:
    return Health(version="0.0.1", status="OK")
