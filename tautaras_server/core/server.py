from fastapi import FastAPI, Request
from api import router
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from fastapi.responses import JSONResponse

from core.config.log_config import setup_logging
from core.exceptions.base import CustomException
from core.infra.cache.cache_manager import Cache
from core.infra.cache.redis_backend import RedisBackend

def init_routers(app_ : FastAPI) -> None:
    app_.include_router(router)


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.code,
            content={"error_code": exc.error_code, "message": exc.message},
        )


def make_middleware() -> List[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]
    return middleware


def init_cache() -> None:
    Cache.init(backend=RedisBackend())


def create_app() -> None:
    app_ = FastAPI(
        title="tautaras is a web crawler",
        description="This crawler is specifically build to extract review from amazon and flipkart",
        version="0.0.1",
        middleware=make_middleware(),
    )
    init_routers(app_=app_)
    init_listeners(app_=app_)
    init_cache()
    setup_logging()

    return app_

app = create_app()
