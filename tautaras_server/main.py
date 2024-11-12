import uvicorn
from typer import Typer, Option
from typing import Optional
from core.config.env_config import sttgs


cli_app = Typer()

port_help = "The port on which to run the Uvicorn server (default is 80)."
auto_relode_help = "Enable auto-reload for the server (useful in development)."


@cli_app.command()
def run_uvicorn_server(
    port: Optional[int] = Option(None, help=port_help),
    auto_reload_server: bool = Option(False, help=auto_relode_help),
    host=sttgs.get("BACKEND_HOST"),
):

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
