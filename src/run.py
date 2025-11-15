from logging import Formatter

import uvicorn
from fastapi import FastAPI
from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger

from .config import settings
from .main import app


class GunicornLogger(Logger):
    def setup(self, cfg) -> None:
        super().setup(cfg)

        self._set_handler(
            log=self.access_log,
            output=cfg.accesslog,
            fmt=Formatter(fmt=settings.logging.log_format),
        )
        self._set_handler(
            log=self.error_log,
            output=cfg.errorlog,
            fmt=Formatter(fmt=settings.logging.log_format),
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
