from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8")
    # API
    base_url: str
    cors_origin: str = "https://uitodo.netlify.app"

    # Database
    mongo_url: SecretStr
    mongo_db: str

    # Auth
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    secret_key: SecretStr


settings = Settings()  # type: ignore[call-arg]
