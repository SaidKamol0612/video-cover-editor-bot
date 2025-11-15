import logging

from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    https_host: str
    port: int = 8080
    webhook_path: str = "/webhook"

    @property
    def webhook_url(self) -> str:
        return f"{self.https_host}{self.webhook_path}"


class BotConfig(BaseModel):
    token: str


class GunicornConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    timeout: int = 900


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    log_format: str = (
        "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
    )
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    log_file: str = "bot.log"

    @property
    def log_level_value(self) -> int:
        return getattr(logging, self.log_level.upper(), logging.INFO)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="CONFIG__",
        env_file=BASE_DIR / ".env",
        env_nested_delimiter="__",
    )

    DEBUG: bool = False

    app: AppConfig
    bot: BotConfig
    gunicorn: GunicornConfig = GunicornConfig()
    logging: LoggingConfig = LoggingConfig()


settings = Settings()
