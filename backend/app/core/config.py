from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", secrets_dir="/mnt/secrets")

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

    # --- Azure OpenAI (chat + embeddings) ---
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072

    # --- Azure AI Search (retrieval) ---
    azure_search_endpoint: str = ""
    azure_search_api_key: str = ""
    azure_search_index: str = "mecha-haruka"
    rag_top_k: int = 5

    # --- Observability (OpenTelemetry -> Azure Monitor / Application Insights) ---
    applicationinsights_connection_string: str = ""
    otel_service_name: str = "mecha-haruka-backend"

    @property
    def chat_configured(self) -> bool:
        """True when the Azure OpenAI + AI Search settings needed for /chat exist."""
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_search_endpoint
            and self.azure_search_api_key
        )


settings = Settings()
