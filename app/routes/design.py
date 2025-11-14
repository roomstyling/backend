from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
from typing import List
from pathlib import Path
from ..models.schemas import (
    StyleOption,
    DesignRequest,
    DesignResponse,
    RoomAnalysis,
    DesignGuide
)
from ..services.gemini_service import get_gemini_service

router = APIRouter(prefix="/api", tags=["design"])

# 업로드 디렉토리 (절대 경로)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 미리 정의된 스타일 옵션
STYLE_OPTIONS = [
    StyleOption(
        id="minimalist",
        name="미니멀리스트",
        description="깔끔하고 단순한 디자인. 필수적인 가구만 배치하고 여백을 강조합니다."
    ),
    StyleOption(
        id="scandinavian",
        name="스칸디나비안",
        description="밝고 자연스러운 북유럽 스타일. 화이트와 우드 톤 중심의 따뜻한 공간."
    ),
    StyleOption(
        id="modern",
        name="모던",
        description="현대적이고 세련된 디자인. 심플하면서도 기능적인 가구와 중성 색상."
    ),
    StyleOption(
        id="vintage",
        name="빈티지",
        description="레트로 감성의 따뜻한 공간. 앤틱 가구와 부드러운 색감."
    ),
    StyleOption(
        id="industrial",
        name="인더스트리얼",
        description="도시적이고 거친 매력. 노출 천장, 벽돌, 금속 소재 활용."
    ),
]


@router.get("/styles", response_model=List[StyleOption])
async def get_styles():
    """사용 가능한 인테리어 스타일 목록 반환"""
    return STYLE_OPTIONS


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """원룸 사진 업로드"""
    try:
        # 파일 확장자 검증
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}"
            )

        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # 파일 저장
        with open(str(file_path), "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return JSONResponse(content={
            "success": True,
            "filename": unique_filename,
            "message": "이미지가 성공적으로 업로드되었습니다."
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.post("/analyze")
async def analyze_room(image_filename: str):
    """원룸 사진 분석"""
    try:
        file_path = UPLOAD_DIR / image_filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다.")

        gemini = get_gemini_service()
        analysis = await gemini.analyze_room(str(file_path))

        return JSONResponse(content={
            "success": True,
            "analysis": analysis
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


@router.post("/design", response_model=DesignResponse)
async def generate_design(request: DesignRequest):
    """인테리어 디자인 가이드 생성"""
    try:
        file_path = UPLOAD_DIR / request.image_filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다.")

        # 스타일 검증
        style = next((s for s in STYLE_OPTIONS if s.id == request.style_id), None)
        if not style:
            raise HTTPException(status_code=400, detail="유효하지 않은 스타일 ID입니다.")

        gemini = get_gemini_service()

        # 1. 방 분석
        analysis_data = await gemini.analyze_room(str(file_path))
        analysis = RoomAnalysis(**analysis_data)

        # 2. 디자인 가이드 생성
        guide_data = await gemini.generate_design_guide(
            str(file_path),
            analysis_data,
            style.name
        )

        guide = DesignGuide(
            style=style.name,
            analysis=analysis,
            recommendations=guide_data.get("recommendations", []),
            layout_suggestions=guide_data.get("layout_suggestions", ""),
            color_scheme=guide_data.get("color_scheme", ""),
            furniture_suggestions=guide_data.get("furniture_suggestions", [])
        )

        return DesignResponse(
            success=True,
            message="디자인 가이드가 성공적으로 생성되었습니다.",
            guide=guide
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"디자인 생성 실패: {str(e)}")


@router.post("/generate-image")
async def generate_interior_image(request: DesignRequest):
    """인테리어 스타일이 적용된 이미지 생성"""
    try:
        file_path = UPLOAD_DIR / request.image_filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다.")

        # 스타일 검증
        style = next((s for s in STYLE_OPTIONS if s.id == request.style_id), None)
        if not style:
            raise HTTPException(status_code=400, detail="유효하지 않은 스타일 ID입니다.")

        gemini = get_gemini_service()

        # 인테리어 이미지 생성
        generated_filename = await gemini.generate_interior_image(
            str(file_path),
            style.name,
            style.description
        )

        if not generated_filename:
            raise HTTPException(status_code=500, detail="이미지 생성에 실패했습니다.")

        return JSONResponse(content={
            "success": True,
            "message": "인테리어 이미지가 성공적으로 생성되었습니다.",
            "generated_image": generated_filename,
            "original_image": request.image_filename,
            "style": style.name
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")


@router.get("/images/{filename}")
async def get_image(filename: str):
    """생성된 이미지 파일 반환"""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")

    return FileResponse(str(file_path))
