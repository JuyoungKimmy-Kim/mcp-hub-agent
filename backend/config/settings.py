"""애플리케이션 설정 관리 모듈"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

# backend/.env 파일 경로
ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """환경 변수 기반 애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: Literal["development", "production"] = "development"
    APP_NAME: str = "MCP Hub Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM API Keys
    GOOGLE_API_KEY: str  # Gemini (개발 환경)
    OPENAI_API_KEY: str  # GPT (프로덕션 환경)

    # Model Selection
    MODEL_NAME_DEV: str = "gemini-2.0-flash-exp"
    MODEL_NAME_PROD: str = "gpt-4o"

    @property
    def model_name(self) -> str:
        """현재 환경에 맞는 모델 이름 반환"""
        return self.MODEL_NAME_PROD if self.APP_ENV == "production" else self.MODEL_NAME_DEV

    @property
    def llm_api_key(self) -> str:
        """현재 환경에 맞는 API 키 반환"""
        return self.OPENAI_API_KEY if self.APP_ENV == "production" else self.GOOGLE_API_KEY

    # MCP Hub Web (Frontend)
    WEB_URL_DEV: str
    WEB_URL_PROD: str

    # MCP Hub MCP Server (SSE)
    MCP_HUB_SERVER_URL_DEV: str
    MCP_HUB_SERVER_URL_PROD: str

    # Additional MCP Servers (optional)
    ANALYTICS_MCP_URL_DEV: str | None = None
    ANALYTICS_MCP_URL_PROD: str | None = None
    CHART_MCP_URL_DEV: str | None = None
    CHART_MCP_URL_PROD: str | None = None

    # MCP Connection Settings
    MCP_SERVER_TIMEOUT: int = 30

    @property
    def web_url(self) -> str:
        """현재 환경에 맞는 웹 URL 반환"""
        return self.WEB_URL_PROD if self.APP_ENV == "production" else self.WEB_URL_DEV

    @property
    def mcp_hub_server_url(self) -> str:
        """현재 환경에 맞는 MCP Hub 서버 URL 반환 (SSE)"""
        return self.MCP_HUB_SERVER_URL_PROD if self.APP_ENV == "production" else self.MCP_HUB_SERVER_URL_DEV

    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins를 리스트로 변환"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str | None = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    CACHE_TYPE: Literal["memory", "redis"] = "memory"
    REDIS_URL: str | None = None

    # Frontend (built static files)
    STATIC_FILES_DIR: str = "../frontend/dist"


# 싱글톤 인스턴스
settings = Settings()
