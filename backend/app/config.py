from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8")
    mongo_url: SecretStr
    mongo_db: str


settings = Settings()  # type: ignore[call-arg]
