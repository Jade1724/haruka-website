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

    # --- Azure OpenAI (chat generation only; embeddings are local now) ---
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = "gpt-4o"

    # --- Local embeddings (sentence-transformers, replaces Azure OpenAI) ---
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"
    local_embedding_query_prefix: str = (
        "Represent this sentence for searching relevant passages: "
    )
    embedding_dimensions: int = 384

    # --- pgvector retrieval (Postgres on the Pi; replaces Azure AI Search) ---
    database_url: str = ""
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
        """True when chat is enabled, Azure OpenAI (generation) is set, and the
        pgvector store (retrieval) is reachable."""
        return bool(
            self.chat_enabled
            and self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.database_url
        )

    @property
    def safety_configured(self) -> bool:
        """True when Azure AI Content Safety is configured (optional; chat runs without it)."""
        return bool(self.azure_content_safety_endpoint and self.azure_content_safety_key)


settings = Settings()
