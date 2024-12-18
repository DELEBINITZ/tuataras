from fastapi import APIRouter
from .review import reviews_router

crawler_routers = APIRouter()

crawler_routers.include_router(reviews_router, prefix="/reviews", tags=["reviews"])


__all__ = ["crawler_routers"]
