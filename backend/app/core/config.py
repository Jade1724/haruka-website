from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    github_token: str
    github_repo: str = "Jade1724/obsidian"
    journals_base_path: str = "Dev/Journals"
    cache_ttl_seconds: int = 600

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    contact_recipient: str

    allowed_origins: str = "http://localhost:3000"


settings = Settings()
