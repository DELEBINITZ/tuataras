from fastapi import APIRouter
from .health_check import health_router

monitoring_routers = APIRouter()

monitoring_routers.include_router(health_router, prefix="/health", tags=["monitoring"])

__all__ = ["monitoring_routers"]
