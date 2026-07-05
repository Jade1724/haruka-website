from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir="/mnt/secrets",
        extra="ignore",
    )

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

    # Log verbosity: DEBUG | INFO | WARNING | ERROR. DEBUG also un-mutes SDK logs.
    log_level: str = "INFO"

    # --- RAG chatbot (mecha-haruka) feature flag ---
    # Off by default: running the chatbot costs money (Azure OpenAI + AI Search).
    # Must be explicitly set to true to enable /chat, even if Azure creds below
    # are present.
    chat_enabled: bool = False

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

    # --- Azure AI Content Safety (Prompt Shields + harmful-content checks) ---
    azure_content_safety_endpoint: str = ""
    azure_content_safety_key: str = ""
    content_safety_threshold: int = 4  # severity levels 0/2/4/6; block >= threshold

    # --- Observability (OpenTelemetry -> Azure Monitor / Application Insights) ---
    applicationinsights_connection_string: str = ""
    otel_service_name: str = "mecha-haruka-backend"

    @property
    def chat_configured(self) -> bool:
        """True when chat is explicitly enabled and its Azure settings exist."""
        return bool(
            self.chat_enabled
            and self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_search_endpoint
            and self.azure_search_api_key
        )

    @property
    def safety_configured(self) -> bool:
        """True when Azure AI Content Safety is configured (optional; chat runs without it)."""
        return bool(self.azure_content_safety_endpoint and self.azure_content_safety_key)


settings = Settings()
