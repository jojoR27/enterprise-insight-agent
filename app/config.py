from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目配置对象
class Settings(BaseSettings):
    app_name: str = "Enterprise Insight Agent"
    app_env: str = "development"

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

# 配置加载一次，后面重复使用
@lru_cache
def get_settings() -> Settings:
    return Settings()