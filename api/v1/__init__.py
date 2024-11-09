from fastapi import APIRouter

from .crawler import crawler_routers
from .monitoring import monitoring_routers

v1_router = APIRouter()

v1_router.include_router(crawler_routers, prefix="")
v1_router.include_router(monitoring_routers, prefix="/monitoring")
