import uvicorn

from unloop.core.config import Settings


def run() -> None:
    settings = Settings()
    uvicorn.run("unloop.api.app:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    run()
