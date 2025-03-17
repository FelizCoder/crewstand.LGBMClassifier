from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.logger import logger


def read_version():
    """Read the version from `version.txt` inside the root directory."""
    with open("version.txt", "r", encoding="utf-8") as file:
        return file.read().strip()


class Config(BaseSettings):
    """Holds configuration settings for the project."""

    BACKEND_BASE: str
    DEBUG_LEVEL: str = "INFO"
    INFLUXDB_BUCKET: str
    INFLUXDB_ORG: str
    INFLUXDB_TOKEN: str
    INFLUXDB_URL: HttpUrl
    PROJECT_NAME: str = "crewstand LightGBM Classifier"
    VERSION: str = read_version()

    model_config = SettingsConfigDict(env_file=".env.local")


config = Config()

logger.setLevel(config.DEBUG_LEVEL.upper())
logger.info(
    "Start project with current configuration \n %s", config.model_dump_json(indent=2)
)
