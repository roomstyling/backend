from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
import asyncio
import time
from typing import List, Dict, Any
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

        # 인테리어 이미지 생성 (이미지 + 분석 텍스트)
        result = await gemini.generate_interior_image(
            str(file_path),
            style.name,
            style.description
        )

        if not result or not result.get('filename'):
            raise HTTPException(status_code=500, detail="이미지 생성에 실패했습니다.")

        return JSONResponse(content={
            "success": True,
            "message": "인테리어 이미지가 성공적으로 생성되었습니다.",
            "generated_image": result['filename'],
            "original_image": request.image_filename,
            "style": style.name,
            "analysis": result.get('analysis', '')
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


@router.post("/get_styled_images")
async def get_styled_images(file: UploadFile = File(...)):
    """
    이미지 1개를 업로드하면 모든 스타일(5개)의 합성 결과를 15초 이내에 반환

    Returns:
        {
            "success": bool,
            "original_image": str,
            "processing_time": float,
            "results": [
                {
                    "style_id": str,
                    "style_name": str,
                    "generated_image": str,
                    "analysis": str,
                    "success": bool,
                    "error": str (optional)
                }
            ]
        }
    """
    start_time = time.time()

    try:
        # 1. 파일 검증 및 저장
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

        # 2. 모든 스타일에 대해 병렬로 이미지 생성 (동시 요청 수 제한)
        gemini = get_gemini_service()

        # Gemini API Rate Limiting 방지: 동시에 최대 2개만 요청
        semaphore = asyncio.Semaphore(2)

        async def generate_for_style(style: StyleOption, max_retries: int = 2) -> Dict[str, Any]:
            """단일 스타일에 대한 이미지 생성 (Retry 로직 포함)"""
            async with semaphore:
                for attempt in range(max_retries):
                    try:
                        result = await gemini.generate_interior_image(
                            str(file_path),
                            style.name,
                            style.description
                        )

                        return {
                            "style_id": style.id,
                            "style_name": style.name,
                            "generated_image": result.get('filename', ''),
                            "analysis": result.get('analysis', ''),
                            "success": True
                        }
                    except Exception as e:
                        error_msg = str(e)
                        # 503 에러거나 rate limit 에러면 재시도
                        if ("503" in error_msg or "rate" in error_msg.lower() or "quota" in error_msg.lower()) and attempt < max_retries - 1:
                            wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s
                            print(f"Rate limit hit for {style.name}, retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue

                        # 최종 실패
                        return {
                            "style_id": style.id,
                            "style_name": style.name,
                            "generated_image": "",
                            "analysis": "",
                            "success": False,
                            "error": error_msg
                        }

        # 3. 병렬 실행 with 20초 타임아웃 (재시도 고려)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[generate_for_style(style) for style in STYLE_OPTIONS]),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            # 타임아웃 발생 시 부분 결과 반환
            raise HTTPException(
                status_code=408,
                detail="이미지 생성 시간이 20초를 초과했습니다. 일부 스타일은 생성되지 않았을 수 있습니다."
            )

        processing_time = time.time() - start_time

        return JSONResponse(content={
            "success": True,
            "original_image": unique_filename,
            "processing_time": round(processing_time, 2),
            "results": results
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 실패: {str(e)}")
