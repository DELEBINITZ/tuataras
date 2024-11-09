from fastapi import FastAPI
from api import router

def init_routers(app_ : FastAPI) -> None:
  app_.include_router(router)


def create_app() -> None:
  app_ = FastAPI(
    title="tautaras is a web crawler",
    description="This crawler is specifically build to extract review from amazon and flipkart",
    version="0.0.1"
  )
  init_routers(app_=app_)
  return app_

app = create_app()



