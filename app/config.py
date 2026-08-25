# 把原来写在.env的配置信息装进 配置对象中 方便统一管理.env整个项目的配置

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目配置对象
class Settings(BaseSettings):
    app_name: str = "Enterprise Insight Agent"
    app_env: str = "development"

    database_url: str
    langgraph_database_url: str

    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimension: int = 512

    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None

    text2sql_database_url: str
    text2sql_max_rows: int = 100
    text2sql_statement_timeout_ms: int = 3000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

# 这里统一创建一次Setting(),再用@lru_cache缓存，整个项目重复使用
# 如果每个模块都直接Settings()实例化对象，那么每个模块都可能重新创建、重新读取一次配置。
@lru_cache
def get_settings() -> Settings:
    return Settings()