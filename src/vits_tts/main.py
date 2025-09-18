import uvicorn
from .app import create_app
from .config import get_server_config

app = create_app()

if __name__ == "__main__":
    server_config = get_server_config()
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8888)

    uvicorn.run(app, host=host, port=port)
