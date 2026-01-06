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

    # Mem0
    mem0_api_key: str = ""

    # OpenAI (for LangChain)
    openai_api_key: str = ""

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


@lru_cache()
def get_settings() -> Settings:
    return Settings()
