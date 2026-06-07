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

    # App
    username_base_len: int = 12
    username_suffix_len: int = 6

    # Database
    mongo_url: SecretStr
    mongo_db: str = "todolist"

    # Auth
    access_token_expire_minutes: int = 30
    reset_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    secret_key: SecretStr

    # Google
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # Github
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str

    # OAuth
    frontend_url: str

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
