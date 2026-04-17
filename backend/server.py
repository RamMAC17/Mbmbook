"""MBM Book Server entry point."""

import uvicorn
from backend.core.config import settings


def main():
    uvicorn.run(
        "backend.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        ws="websockets",
    )


if __name__ == "__main__":
    main()
