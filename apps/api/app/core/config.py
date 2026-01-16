from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from urllib.parse import quote_plus
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Application
    app_name: str = "Manufacturing Performance Assistant"
    debug: bool = False

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # MSSQL (Read-Only) - Individual environment variables
    mssql_server: str = ""
    mssql_database: str = ""
    mssql_user: str = ""
    mssql_password: str = ""
    mssql_port: int = 1433
    mssql_driver: str = "ODBC Driver 18 for SQL Server"

    # Connection Pool Settings
    mssql_pool_size: int = 5
    mssql_max_overflow: int = 10
    mssql_pool_timeout: int = 30

    # Mem0 Configuration (Story 4.1)
    mem0_api_key: str = ""
    supabase_db_url: str = ""  # Direct PostgreSQL connection string for Mem0
    mem0_collection_name: str = "memories"
    mem0_embedding_dims: int = 1536
    mem0_top_k: int = 5
    mem0_similarity_threshold: float = 0.7

    # OpenAI (for LangChain and Mem0 embeddings)
    openai_api_key: str = ""

    # Text-to-SQL Configuration (Story 4.2)
    sql_query_timeout: int = 30  # Max query execution seconds
    sql_max_rows: int = 100  # Max rows returned
    chat_rate_limit_requests: int = 10  # Requests per window
    chat_rate_limit_window: int = 60  # Window in seconds

    # Pipeline Configuration
    pipeline_timezone: str = "America/Chicago"
    safety_reason_code: str = "Safety Issue"
    pipeline_retry_count: int = 3
    pipeline_log_level: str = "INFO"

    # Financial Configuration (Story 2.7)
    default_hourly_rate: float = 100.00
    default_cost_per_unit: float = 10.00
    financial_currency: str = "USD"

    # Action Engine Configuration (Story 3.1)
    target_oee_percentage: float = 85.0
    financial_loss_threshold: float = 1000.0
    oee_high_gap_threshold: float = 20.0
    oee_medium_gap_threshold: float = 10.0
    financial_high_threshold: float = 5000.0
    financial_medium_threshold: float = 2000.0

    # Agent Configuration (Story 5.1)
    llm_provider: str = "openai"  # LLM provider selection (openai/anthropic)
    llm_model: str = "gpt-4-turbo-preview"  # Model identifier
    agent_temperature: float = 0.1  # Lower for more deterministic tool selection
    agent_max_iterations: int = 5  # Prevent runaway agent loops
    agent_verbose: bool = False  # Debug logging for agent
    agent_timeout_seconds: int = 60  # Agent execution timeout
    agent_rate_limit_requests: int = 10  # Rate limit requests per window
    agent_rate_limit_window: int = 60  # Rate limit window in seconds

    # Data Source Configuration (Story 5.2)
    data_source_type: str = "supabase"  # Data source type: "supabase" or "composite"

    # Cache Configuration (Story 5.8)
    cache_enabled: bool = True  # Enable/disable tool response caching
    cache_max_size: int = 1000  # Max entries per cache tier
    cache_live_ttl: int = 60  # Live tier TTL in seconds (1 minute)
    cache_daily_ttl: int = 900  # Daily tier TTL in seconds (15 minutes)
    cache_static_ttl: int = 3600  # Static tier TTL in seconds (1 hour)

    # ElevenLabs TTS Configuration (Story 8.1)
    elevenlabs_api_key: str = ""  # ElevenLabs API key
    elevenlabs_model: str = "eleven_flash_v2_5"  # Flash v2.5 for low latency
    elevenlabs_voice_id: str = ""  # Default voice ID
    elevenlabs_timeout: int = 10  # Request timeout in seconds

    @property
    def mssql_connection_string(self) -> str:
        """Build MSSQL connection string with proper URL encoding for special characters."""
        if not all([self.mssql_server, self.mssql_database, self.mssql_user, self.mssql_password]):
            return ""

        # URL-encode password to handle special characters
        encoded_password = quote_plus(self.mssql_password)
        encoded_user = quote_plus(self.mssql_user)
        encoded_driver = quote_plus(self.mssql_driver)

        return (
            f"mssql+pyodbc://{encoded_user}:{encoded_password}"
            f"@{self.mssql_server}:{self.mssql_port}/{self.mssql_database}"
            f"?driver={encoded_driver}&TrustServerCertificate=yes"
        )

    @property
    def mssql_configured(self) -> bool:
        """Check if MSSQL connection is properly configured."""
        return all([
            self.mssql_server,
            self.mssql_database,
            self.mssql_user,
            self.mssql_password
        ])

    @property
    def mem0_configured(self) -> bool:
        """Check if Mem0 memory service is properly configured (Story 4.1 AC#1)."""
        return all([
            self.supabase_db_url,
            self.openai_api_key
        ])

    @property
    def agent_configured(self) -> bool:
        """Check if Agent is properly configured (Story 5.1 AC#1)."""
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return False

    @property
    def data_source_configured(self) -> bool:
        """Check if data source is properly configured (Story 5.2 AC#5)."""
        if self.data_source_type == "supabase":
            return all([self.supabase_url, self.supabase_key])
        elif self.data_source_type == "composite":
            # Composite requires at least Supabase as primary
            return all([self.supabase_url, self.supabase_key])
        return False

    @property
    def elevenlabs_configured(self) -> bool:
        """Check if ElevenLabs TTS is properly configured (Story 8.1 AC#1)."""
        return bool(self.elevenlabs_api_key)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
