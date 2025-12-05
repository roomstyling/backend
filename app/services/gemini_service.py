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
        style: str,
        style_description: str,
        room_analysis: Optional[Dict[str, Any]] = None
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

            # 방 분석 정보 추가 (있는 경우)
            analysis_context = ""
            if room_analysis:
                analysis_context = f"""
ROOM ANALYSIS (ABSOLUTELY PRESERVE - DO NOT CHANGE):
- Structure: {room_analysis.get('room_structure', 'N/A')}
- Layout: {room_analysis.get('spatial_layout', 'N/A')}
- Building Materials: {room_analysis.get('current_materials', 'N/A')}
- Key Features: {', '.join(room_analysis.get('key_features', []))}
- Constraints: {', '.join(room_analysis.get('constraints', []))}

CRITICAL RULES:
1. NEVER modify room structure (walls, windows, doors, ceiling, floor boundaries)
2. You CAN change furniture arrangement and items completely
3. Select furniture that harmonizes with the fixed building materials
"""

            # 이미지 생성 중심 프롬프트 (간결하고 명확하게)
            prompt = f"""IMPORTANT: You MUST generate an image. Do not provide text-only response.

Transform this room into {style} style interior design.

Style essence: {style_info['essence']}
Approach: {style_info['approach']}
{analysis_context}
IMAGE GENERATION REQUIREMENTS:

ROOM STRUCTURE (ABSOLUTELY FORBIDDEN TO CHANGE):
1. NEVER modify walls, windows, doors positions - keep EXACTLY as original
2. NEVER change ceiling height, floor boundaries, or room dimensions
3. NEVER add or remove architectural elements (columns, beams, moldings)
4. PRESERVE the exact spatial layout and room proportions
5. FIXED building materials (floor/wall/ceiling finishes) must stay visually consistent
6. CRITICAL: Keep the SAME camera angle and viewpoint as the original photo
   - Do NOT change the perspective or shooting angle
   - Maintain the exact same framing and composition
   - Keep the same field of view and camera position

FURNITURE & DECOR (FREELY CHANGEABLE):
7. You MUST change and redesign all furniture to match {style} style
8. Place specific, identifiable furniture items: desk, chair, shelves, curtains, lighting, rugs, etc.
9. Each furniture piece must be clearly visible and realistic (suitable for product links)
10. Ensure furniture complements the FIXED building materials:
   - Wood floors → select furniture with compatible wood tones
   - Concrete walls → choose furniture with industrial/modern textures
   - Create visual harmony between fixed materials and movable furniture
11. Make furniture look purchasable and realistic (avoid abstract/artistic renderings)

STYLE GUIDELINES:
- Reflect core characteristics of {style} style
- Create a natural and realistic space suitable for real living
- Avoid over-decoration - keep it practical and livable
- Focus ONLY on furniture/decor changes, NOT architectural changes

OUTPUT REQUIREMENTS:
- Generate the transformed room image with {style} style furniture and decor
- Keep the SAME room structure (walls, windows, doors, dimensions)
- Show clear, identifiable furniture pieces that could be sold/linked
- Ensure visual harmony between fixed building materials and new furniture

CRITICAL FINAL CHECK:
1. Room structure unchanged? (walls, windows, doors in same positions)
2. Camera angle and viewpoint identical to original photo?
3. Furniture clearly visible and realistic?
4. Building materials and furniture harmonize well?

If YES to all four → Generate the image now.
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
