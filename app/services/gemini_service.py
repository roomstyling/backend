import os
import google.generativeai as genai_old
from google import genai
from google.genai import types
from PIL import Image
from typing import Dict, Any, Optional
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
        self.model = genai_old.GenerativeModel('gemini-2.5-flash-image-preview')

        # 신버전 Gemini 클라이언트 (이미지 생성용)
        self.client = genai.Client(api_key=settings.gemini_api_key)

        logger.info("GeminiService initialized")

    async def analyze_room(self, image_path: str) -> Dict[str, Any]:
        """원룸 사진 분석 (JSON mode)"""
        try:
            logger.info(f"Analyzing room: {image_path}")
            img = Image.open(image_path)

            prompt = """
            이 원룸 사진을 분석해주세요. JSON 형식으로 답변하세요.

            {
                "room_type": "원룸/투룸 등 방 타입",
                "size_estimate": "평수 추정",
                "current_layout": "현재 레이아웃 설명",
                "issues": ["문제점1", "문제점2"],
                "strengths": ["장점1", "장점2"]
            }
            """

            # JSON mode 사용
            response = self.model.generate_content(
                [prompt, img],
                generation_config=genai_old.GenerationConfig(
                    response_mime_type="application/json"
                )
            )

            result = json.loads(response.text)
            logger.info(f"Room analysis completed: {result.get('room_type', 'unknown')}")
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
            이 원룸에 대한 {style} 인테리어 디자인 가이드를 JSON으로 작성해주세요.

            현재 분석: {json.dumps(analysis, ensure_ascii=False)}

            JSON 형식:
            {{
                "recommendations": ["추천1", "추천2"],
                "layout_suggestions": "레이아웃 제안",
                "color_scheme": "색상 제안",
                "furniture_suggestions": ["가구1", "가구2"]
            }}
            """

            response = self.model.generate_content(
                [prompt, img],
                generation_config=genai_old.GenerationConfig(
                    response_mime_type="application/json"
                )
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
        style: str,
        style_description: str
    ) -> dict:
        """인테리어 스타일이 적용된 이미지 생성 (Gemini 2.5 Flash Image 사용)

        Returns:
            dict: {
                'filename': 생성된 이미지 파일명,
                'analysis': 분석 및 변경 내용 텍스트
            }
        """
        try:
            # 원본 이미지 로드
            original_image = Image.open(image_path)

            # 스타일별 핵심 감성 및 접근법
            style_essence = {
                "미니멀리스트": {
                    "essence": "Less is more. 공간의 여백이 주는 평온함과 심플한 라인의 우아함",
                    "approach": "불필요한 것을 덜어내되, 남은 것은 완벽하게. 기능과 미학의 조화"
                },
                "스칸디나비안": {
                    "essence": "자연광과 나무의 따뜻함, 휘게(Hygge) 문화의 아늑함",
                    "approach": "자연 소재와 밝은 톤으로 북유럽의 여유로움을 담아내기"
                },
                "모던": {
                    "essence": "현대적 세련미와 기하학적 정교함, 도시적 감각",
                    "approach": "깔끔한 라인과 중성적 색감으로 시대를 초월하는 모던함 표현"
                },
                "빈티지": {
                    "essence": "시간이 만들어낸 이야기와 감성, 레트로의 낭만",
                    "approach": "앤티크한 디테일과 따뜻한 색감으로 추억을 불러일으키는 공간"
                },
                "인더스트리얼": {
                    "essence": "날것의 재료가 주는 솔직함과 거친 매력, 도시 로프트 감성",
                    "approach": "노출된 구조와 원자재의 질감으로 날것의 아름다움 강조"
                }
            }

            style_info = style_essence.get(style, {
                "essence": style_description,
                "approach": "공간의 가능성을 최대한 이끌어내기"
            })

            # 이미지 생성 중심 프롬프트 (간결하고 명확하게)
            prompt = f"""**IMPORTANT: You MUST generate an image. Do not provide text-only response.**

Transform this room into {style} style interior design.

Style essence: {style_info['essence']}
Approach: {style_info['approach']}

**IMAGE GENERATION REQUIREMENTS:**
1. Keep the same room layout and structure
2. Apply {style} style to walls, floors, furniture, and decor
3. Maintain realistic lighting and proportions
4. Make it look professional and livable

**STYLE GUIDELINES:**
- {style} 스타일의 핵심 특징을 반영하세요
- 자연스럽고 현실적인 공간으로 만드세요
- 과도하게 꾸미지 말고 실제 거주 가능한 느낌으로

**OUTPUT:**
- Generate the transformed room image showing {style} style
- Add a brief analysis in Korean (2-3 sentences) explaining the key changes

**CRITICAL: You MUST return an image. Generate the {style} interior design image now.**
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

            # 응답에서 이미지와 텍스트 추출 (간소화)
            parts = response.candidates[0].content.parts if hasattr(response, 'candidates') else response.parts
            analysis_text = ""
            image_data = None

            for part in parts:
                if hasattr(part, 'text') and part.text:
                    analysis_text += part.text
                elif hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data

            if not image_data:
                raise Exception(f"이미지 생성 실패. 텍스트만 반환됨: {analysis_text[:100] if analysis_text else 'N/A'}")

            # 이미지 저장 (raw bytes, base64 없음)
            image = Image.open(BytesIO(image_data))
            image.save(str(output_path))

            logger.info(f"{style} 이미지 생성 성공: {filename}")
            return {
                'filename': filename,
                'analysis': analysis_text.strip() if analysis_text else "분석 내용이 생성되지 않았습니다."
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
