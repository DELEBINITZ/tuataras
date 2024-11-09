import uvicorn
from typer import Typer, Option
from typing import Optional
from core.infra._celery import start_celery_worker
from core.config import sttgs

cli_app = Typer()

port_help = "The port on which to run the Uvicorn server (default is 80)."
auto_relode_help = "Enable auto-reload for the server (useful in development)."
debug_celery_help = "Enable debugging for Celery tasks."


@cli_app.command()
def run_uvicorn_server(
    port: Optional[int] = Option(None, help=port_help),
    auto_reload_server: bool = Option(False, help=auto_relode_help),
    debug_celery: bool = Option(False, help=debug_celery_help),
    host=sttgs.get("BACKEND_HOST", "0.0.0.0"),
):
    """Run the FastAPI app using Uvicorn, with optional debugging and reloading."""

    celery_worker_process = start_celery_worker(debug=debug_celery)

    backend_port = port if port else sttgs.get("BACKEND_PORT", 80)

    uvicorn.run(
        app="core.server:app",
        reload=auto_reload_server,
        port=backend_port,
        workers=1,
        host=host,
    )


if __name__ == "__main__":
    cli_app() 
