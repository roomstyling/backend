"""애플리케이션 설정"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """환경변수 기반 설정"""

    # API Keys
    gemini_api_key: str

    # Application
    app_name: str = "Interior Design API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # File Upload
    max_upload_size_mb: int = 10
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".webp"]

    # Gemini API
    gemini_concurrent_requests: int = 5  # 5개 스타일 모두 병렬 처리
    gemini_retry_attempts: int = 3  # 3회 재시도 (이미지 생성 실패 대비)
    gemini_timeout_seconds: int = 60  # 보수적으로 60초 설정 (Gemini 3 Pro는 더 느림)

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()
