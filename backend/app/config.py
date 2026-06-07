from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8")
    # API
    api_title: str = "Todo API"
    api_version: str = "1.0.0"
    api_docs_url: str = "https://github.com/viraj-sh/todo"
    base_url: str
    cors_origin: str = "https://uitodo.netlify.app"
    frontend_url: str = "https://uitodo.netlify.app"

    # Database
    mongo_url: SecretStr
    mongo_db: str = "todolist"

    # Auth
    access_token_expire_minutes: int = 30
    reset_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    secret_key: SecretStr

    # ApiKey
    max_api_key_count: int = 5

    # Mail
    mail_from: str
    mail_host: str
    mail_port: int
    mail_username: str
    mail_password: SecretStr
    use_tls: bool = True


settings = Settings()  # type: ignore
