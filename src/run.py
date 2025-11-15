import logging
from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger

from .config import settings
from .main import app, bot, dp


class GunicornLogger(Logger):
    def setup(self, cfg) -> None:
        super().setup(cfg)

        self._set_handler(
            log=self.access_log,
            output=cfg.accesslog,
            fmt=logging.Formatter(
                fmt=settings.logging.log_format,
                datefmt=settings.logging.log_date_format,
            ),
        )
        self._set_handler(
            log=self.error_log,
            output=cfg.errorlog,
            fmt=logging.Formatter(
                fmt=settings.logging.log_format,
                datefmt=settings.logging.log_date_format,
            ),
        )


def get_app_options(
    host: str,
    port: int,
    timeout: int,
    workers: int,
    log_level: str,
) -> dict:
    return {
        "accesslog": "-",
        "errorlog": "-",
        "bind": f"{host}:{port}",
        "loglevel": log_level,
        "logger_class": GunicornLogger,
        "timeout": timeout,
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }


class Application(BaseApplication):
    def __init__(
        self,
        application: FastAPI,
        options: dict | None = None,
    ):
        self.options = options or {}
        self.application = application
        super().__init__()

    def load(self):
        return self.application

    @property
    def config_options(self) -> dict:
        return {
            # pair
            k: v
            # for each option
            for k, v in self.options.items()
            # not empty key / value
            if k in self.cfg.settings and v is not None  # type: ignore
        }

    def load_config(self):
        for key, value in self.config_options.items():
            self.cfg.set(key.lower(), value)  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(settings.app.webhook_url)
    logging.info(f"Webhook set: {settings.app.webhook_url}")

    yield

    await bot.delete_webhook()
    logging.info("Webhook removed")
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.post(settings.app.webhook_path)
async def telegram_webhook(request: Request):
    try:
        update = Update.model_validate(await request.json())
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.exception(f"Error while processing update: {e}")
    return {"ok": True}


@app.get("/")
async def root():
    return RedirectResponse(url="docs/")


def guniorn_run():
    """
    Run the application with Gunicorn.
    """

    Application(
        application=app,
        options=get_app_options(
            host=settings.gunicorn.host,
            port=settings.gunicorn.port,
            timeout=settings.gunicorn.timeout,
            workers=settings.gunicorn.workers,
            log_level=settings.logging.log_level,
        ),
    ).run()


if __name__ == "__main__":
    guniorn_run()
