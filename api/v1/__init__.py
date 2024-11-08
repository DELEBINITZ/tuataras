from fastapi import APIRouter

from .monitoring import monitoring_routers

v1_router = APIRouter()

v1_router.include_router(monitoring_routers, prefix="/monitoring")
