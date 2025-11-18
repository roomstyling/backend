from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .routes import design
from .config import settings
from .utils.logger import logger

# 프로젝트 루트 디렉토리 (backend 폴더)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# 필요한 디렉토리 생성
for directory in [STATIC_DIR, UPLOAD_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

logger.info(f"Starting {settings.app_name} v{settings.app_version}")

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    description="원룸 인테리어 디자인 가이드 생성 API",
    version=settings.app_version,
    debug=settings.debug
)

# CORS 설정 (환경변수 기반)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS enabled for origins: {settings.cors_origins}")

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 라우터 등록
app.include_router(design.router)


@app.get("/")
async def home(request: Request):
    """홈페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """헬스 체크 및 시스템 상태"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "gemini_api_key_configured": bool(settings.gemini_api_key),
        "config": {
            "max_upload_size_mb": settings.max_upload_size_mb,
            "concurrent_requests": settings.gemini_concurrent_requests,
            "timeout_seconds": settings.gemini_timeout_seconds
        }
    }


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("="*50)
    logger.info("Application startup")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Gemini API configured: {bool(settings.gemini_api_key)}")
    logger.info(f"Max upload size: {settings.max_upload_size_mb}MB")
    logger.info("="*50)


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("Application shutdown")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
