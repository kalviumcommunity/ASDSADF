import uvicorn
from src.config import settings

if __name__ == "__main__":
    uvicorn.run("src.api:app", host=settings.app_host, port=settings.app_port, reload=settings.debug)
import uvicorn
from src.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )