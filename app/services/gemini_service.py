import os
import google.generativeai as genai_old
from google import genai
from google.genai import types
from PIL import Image
from typing import Dict, Any
import json
import base64
from io import BytesIO
from pathlib import Path

from ..config import settings
from ..utils.logger import logger


class GeminiService:
    """Google Gemini API 서비스"""

    def __init__(self):
        # 설정에서 API 키 로드
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        # 구버전 Gemini 모델 (텍스트/분석용)
        genai_old.configure(api_key=settings.gemini_api_key)
        self.model = genai_old.GenerativeModel('gemini-3-pro-preview')

        # 신버전 Gemini 클라이언트 (이미지 생성용)
        self.client = genai.Client(api_key=settings.gemini_api_key)

        logger.info("GeminiService initialized")

    async def analyze_room(self, image_path: str) -> Dict[str, Any]:
        """방 분석 (JSON mode)"""
        try:
            logger.info(f"Analyzing room: {image_path}")

            prompt = """
            Analyze this room photo and respond in JSON format. Provide all text fields in English.

            Focus on structural and spatial characteristics that are important for interior design transformation:

            {
                "room_structure": "Describe walls, windows, doors positions and architectural features in detail",
                "spatial_layout": "Room shape, dimensions, and spatial characteristics",
                "current_materials": "Current building materials (BM) - floors, walls, ceiling finishes",
                "key_features": ["Notable architectural feature 1", "Notable feature 2"],
                "constraints": ["Design constraint 1", "Design constraint 2"]
            }

            Important: All text values must be in English. Focus on structural details and building materials (BM) that must be preserved during redesign.
            """

            # 비동기 처리
            import asyncio
            response = await asyncio.to_thread(
                lambda: self.model.generate_content(
                    [prompt, Image.open(image_path)]
                )
            )

            # JSON 추출 (마크다운 코드 블록 처리)
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            result = json.loads(response_text.strip())
            logger.info(f"Room analysis completed: {result.get('room_structure', 'unknown')[:50]}")
            return result

        except Exception as e:
            logger.error(f"Room analysis failed: {str(e)}", exc_info=True)
            raise Exception(f"이미지 분석 중 오류 발생: {str(e)}")

    async def generate_design_guide(
        self,
        image_path: str,
        analysis: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """인테리어 디자인 가이드 생성 (JSON mode)"""
        try:
            logger.info(f"Generating design guide for {style}")
            img = Image.open(image_path)

            prompt = f"""
            Create an interior design guide for this room in {style} style. Respond in JSON format with all text in Korean.

            Current analysis: {json.dumps(analysis, ensure_ascii=False)}

            JSON format:
            {{
                "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
                "layout_suggestions": "Layout improvement suggestions",
                "color_scheme": "Color palette recommendations",
                "furniture_suggestions": ["Furniture item 1", "Furniture item 2", "Furniture item 3"]
            }}

            Important: All text values in the JSON must be in Korean.
            """

            # 비동기 처리
            import asyncio
            response = await asyncio.to_thread(
                lambda: self.model.generate_content([prompt, img])
            )

            result = json.loads(response.text)
            logger.info(f"Design guide generated for {style}")
            return result

        except Exception as e:
            logger.error(f"Design guide generation failed: {str(e)}", exc_info=True)
            raise Exception(f"디자인 가이드 생성 중 오류 발생: {str(e)}")

    async def generate_interior_image(
        self,
        image_path: str,
        style: str
    ) -> dict:
        """인테리어 스타일이 적용된 이미지 생성 (Gemini 3 Pro Image 사용)

        Returns:
            dict: {
                'filename': 생성된 이미지 파일명,
                'analysis': 분석 및 변경 내용 텍스트
            }
        """
        try:
            # 원본 이미지 로드
            original_image = Image.open(image_path)

            # 이미지 생성 프롬프트
            prompt = f"""Transform this room into {style} style interior design.

CRITICAL: Keep the original room structure intact:
- Same walls, windows, doors, ceiling, floor positions
- Same camera angle and viewpoint
- Same architectural elements

Change only the furniture and decor:
- Replace all furniture to match {style} style
- Make each piece clearly visible and realistic (suitable for product links)
- Ensure furniture harmonizes with the existing building materials
            """

            logger.info(f"Generating {style} image with Gemini 3 Pro")

            # Gemini 3 Pro로 이미지 생성 (비동기 실행)
            import asyncio
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-3-pro-image-preview",
                contents=[prompt, original_image],
            )

            logger.info(f"Response received for {style}")

            # 응답에서 이미지 데이터 추출 및 저장
            import uuid
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            UPLOAD_DIR = BASE_DIR / "uploads"
            UPLOAD_DIR.mkdir(exist_ok=True)

            filename = f"generated_{uuid.uuid4()}.png"
            output_path = UPLOAD_DIR / filename

            # 응답에서 이미지 데이터 추출
            parts = response.candidates[0].content.parts if hasattr(response, 'candidates') else response.parts
            image_data = None

            for part in parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    break

            if not image_data:
                raise Exception(f"이미지 생성 실패. 이미지 데이터를 찾을 수 없습니다.")

            # 이미지 저장 (raw bytes)
            image = Image.open(BytesIO(image_data))
            image.save(str(output_path))

            logger.info(f"{style} 이미지 생성 성공: {filename}")
            return {
                'filename': filename,
                'analysis': ''
            }

        except Exception as e:
            logger.error(f"{style} 이미지 생성 실패: {type(e).__name__}: {str(e)}", exc_info=True)
            raise Exception(f"인테리어 이미지 생성 중 오류 발생: {str(e)}")


# 싱글톤 인스턴스
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """GeminiService 인스턴스 가져오기"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
