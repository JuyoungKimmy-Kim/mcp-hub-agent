"""
MCP Hub Agent - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.utils.logging import LogManager

# 로깅 초기화
LogManager.setup_logging(
    log_level=settings.LOG_LEVEL,
)
logger = LogManager.get_logger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(
        f"Application starting - {settings.APP_NAME} v{settings.APP_VERSION} "
        f"(env={settings.APP_ENV}, model={settings.model_name})"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("Application shutting down")


@app.get("/health")
async def health_check():
    """
    헬스체크 엔드포인트

    Returns:
        dict: 애플리케이션 상태 정보
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "model": settings.model_name,
    }


@app.get("/")
async def root():
    """
    루트 엔드포인트

    Returns:
        dict: 기본 정보
    """
    return {
        "message": "MCP Hub Agent API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
