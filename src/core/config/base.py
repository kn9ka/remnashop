import os
from pathlib import Path

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from src.core.constants import BASE_DIR

DEFAULT_ENV_FILE = BASE_DIR / ".env"
EXTERNAL_ENV_FILE_VARS = ("REMNASHOP_ENV_FILE", "REMNASHOP_ENV_FILES")


def get_env_files() -> tuple[Path, ...]:
    env_files: list[Path] = [DEFAULT_ENV_FILE]

    for env_var in EXTERNAL_ENV_FILE_VARS:
        raw_value = os.getenv(env_var, "").strip()
        if not raw_value:
            continue

        for value in raw_value.replace("\n", ",").split(","):
            path = value.strip()
            if path:
                env_files.append(Path(path))

    return tuple(dict.fromkeys(env_files))


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=get_env_files(),
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Docker environment variables should override any value loaded from env files.
        return init_settings, env_settings, dotenv_settings, file_secret_settings
