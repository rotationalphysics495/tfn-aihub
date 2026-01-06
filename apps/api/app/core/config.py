from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Application
    app_name: str = "Manufacturing Performance Assistant"
    debug: bool = False

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # MSSQL (Read-Only)
    mssql_connection_string: str = ""

    # Mem0
    mem0_api_key: str = ""

    # OpenAI (for LangChain)
    openai_api_key: str = ""


@lru_cache()
def get_settings() -> Settings:
    return Settings()
