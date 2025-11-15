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


class GeminiService:
    """Google Gemini API 서비스"""

    def __init__(self):
        # 환경변수에서 API 키 로드
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

        # 구버전 Gemini 모델 (텍스트/분석용)
        genai_old.configure(api_key=api_key)
        self.model = genai_old.GenerativeModel('gemini-2.5-flash-image-preview')

        # 신버전 Gemini 클라이언트 (이미지 생성용)
        self.client = genai.Client(api_key=api_key)

    async def analyze_room(self, image_path: str) -> Dict[str, Any]:
        """원룸 사진 분석"""
        try:
            img = Image.open(image_path)

            prompt = """
            이 원룸 사진을 분석해주세요. 다음 정보를 JSON 형식으로 제공해주세요:

            {
                "room_type": "원룸/투룸 등",
                "size_estimate": "평수 추정",
                "current_layout": "현재 레이아웃 설명",
                "issues": ["문제점 1", "문제점 2", ...],
                "strengths": ["장점 1", "장점 2", ...]
            }

            특히 다음 사항을 확인해주세요:
            - 방문 옆에 침대가 있는지 (동선 문제)
            - 창문 위치와 채광
            - 공간 활용도
            - 수납 공간
            - 가구 배치의 효율성
            """

            response = self.model.generate_content([prompt, img])

            # JSON 파싱 시도
            try:
                # 마크다운 코드 블록 제거
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]

                result = json.loads(text.strip())
                return result
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 구조 반환
                return {
                    "room_type": "원룸",
                    "size_estimate": "분석 중",
                    "current_layout": response.text,
                    "issues": ["분석 결과를 구조화하지 못했습니다."],
                    "strengths": []
                }

        except Exception as e:
            raise Exception(f"이미지 분석 중 오류 발생: {str(e)}")

    async def generate_design_guide(
        self,
        image_path: str,
        analysis: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """인테리어 디자인 가이드 생성"""
        try:
            img = Image.open(image_path)

            prompt = f"""
            이 원룸에 대한 인테리어 디자인 가이드를 작성해주세요.

            현재 분석 결과:
            - 방 타입: {analysis.get('room_type')}
            - 크기: {analysis.get('size_estimate')}
            - 문제점: {', '.join(analysis.get('issues', []))}
            - 장점: {', '.join(analysis.get('strengths', []))}

            원하는 스타일: {style}

            다음 형식의 JSON으로 답변해주세요:
            {{
                "recommendations": ["추천사항 1", "추천사항 2", ...],
                "layout_suggestions": "레이아웃 제안 상세 설명",
                "color_scheme": "색상 배치 제안",
                "furniture_suggestions": ["가구 제안 1", "가구 제안 2", ...]
            }}

            특히:
            1. 동선을 고려한 가구 배치
            2. 공간을 넓어 보이게 하는 방법
            3. 수납 공간 최적화
            4. 선택한 스타일에 맞는 색상과 소품 제안
            """

            response = self.model.generate_content([prompt, img])

            # JSON 파싱 시도
            try:
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]

                result = json.loads(text.strip())
                return result
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 구조 반환
                return {
                    "recommendations": [response.text],
                    "layout_suggestions": "상세 제안은 텍스트 형식으로 제공되었습니다.",
                    "color_scheme": "분석 중",
                    "furniture_suggestions": []
                }

        except Exception as e:
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

            # 스타일별 상세 가이드라인
            style_guides = {
                "미니멀리스트": """
                - COLOR: Pure white walls, neutral tones (white, beige, light gray)
                - FURNITURE: Simple geometric forms, clean lines, minimal pieces
                - MATERIALS: Natural wood, smooth surfaces, matte finishes
                - DECOR: Almost no decorations, one simple artwork maximum
                - LIGHTING: Recessed lights, simple pendant lamps
                - FLOORING: Light wood or polished concrete
                - RULE: Less is more - remove clutter, keep only essentials
                """,
                "스칸디나비안": """
                - COLOR: White walls, soft pastels (light blue, pale pink, cream)
                - FURNITURE: Light wood (birch, ash), simple Nordic designs
                - MATERIALS: Natural textiles (linen, cotton, wool), untreated wood
                - DECOR: Indoor plants, woven baskets, hygge elements, cozy textiles
                - LIGHTING: Multiple warm light sources, pendant lamps, candles
                - FLOORING: Light blonde wood planks
                - RULE: Functional, cozy, natural light emphasis
                """,
                "모던": """
                - COLOR: Neutral palette (black, white, gray) with one accent color
                - FURNITURE: Sleek contemporary designs, metallic accents, glass
                - MATERIALS: Polished surfaces, chrome, glass, lacquer
                - DECOR: Abstract art, geometric patterns, minimal accessories
                - LIGHTING: Track lighting, modern LED fixtures, statement pieces
                - FLOORING: Large format tiles or dark hardwood
                - RULE: Clean, sophisticated, current trends
                """,
                "빈티지": """
                - COLOR: Warm earth tones (terracotta, sage green, dusty pink, cream)
                - FURNITURE: Antique or vintage-inspired pieces, ornate details
                - MATERIALS: Aged wood, brass, velvet, lace, floral patterns
                - DECOR: Vintage frames, old books, dried flowers, retro items
                - LIGHTING: Vintage chandeliers, Edison bulbs, brass lamps
                - FLOORING: Distressed hardwood or patterned tiles
                - RULE: Nostalgic, romantic, lived-in character
                """,
                "인더스트리얼": """
                - COLOR: Raw (exposed brick, concrete gray, black, rust)
                - FURNITURE: Metal frames, reclaimed wood, utilitarian designs
                - MATERIALS: Exposed brick, concrete, metal pipes, steel, leather
                - DECOR: Edison bulbs, metal signs, industrial clocks, exposed hardware
                - LIGHTING: Cage lights, metal pendants, exposed filament bulbs
                - FLOORING: Concrete or reclaimed wood
                - RULE: Raw, unfinished, urban warehouse aesthetic
                """
            }

            style_guide = style_guides.get(style, "Follow the style description provided.")

            # 이미지 생성 강제 프롬프트
            prompt = f"""
CRITICAL: You MUST generate an edited image. Do not just provide text analysis.

You are a professional interior designer specializing in {style} style.

TASK: Transform this room image to {style} style. Keep the same room structure but apply {style} styling.

{style} STYLE GUIDELINES:
{style_guide}

Style Description: {style_description}

PRESERVATION (DO NOT CHANGE):
- Room dimensions and walls
- Window and door positions/sizes
- Overall furniture layout

APPLY {style} STYLE:
1. Wall colors → {style} palette
2. Furniture materials/finishes → {style} aesthetics
3. Add new furniture if needed (specify in Korean what you added and where)
4. Soft furnishings (curtains, rugs, bedding) → {style} patterns
5. Lighting fixtures → {style} designs
6. Decorative items → {style} accessories
7. Flooring → {style} materials

STRICT ADHERENCE TO {style} STYLE:
- Follow ALL guidelines above for {style}
- Do NOT mix with other styles
- Every element must match {style} aesthetic perfectly

OUTPUT REQUIRED:
1. First: Brief Korean explanation (한국어로):
   - 현재 상태 관찰
   - {style} 스타일 변경 내용
   - 추가한 가구 (구체적으로 명시: 예: "침대 옆에 {style} 스타일 사이드 테이블 추가")

2. Second: GENERATE THE TRANSFORMED IMAGE showing {style} style applied
   - This is MANDATORY - you must produce an edited image
   - Apply all {style} guidelines strictly
   - Keep the same room layout
            """

            print(f"Generating image with prompt: {prompt[:150]}...")

            # Gemini 2.5 Flash Image로 이미지 편집
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, original_image],
            )

            print(f"DEBUG: Response type: {type(response)}")
            print(f"DEBUG: Response attributes: {dir(response)}")

            # 응답에서 이미지 데이터 추출 및 저장
            import uuid
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            UPLOAD_DIR = BASE_DIR / "uploads"
            UPLOAD_DIR.mkdir(exist_ok=True)

            filename = f"generated_{uuid.uuid4()}.png"
            output_path = UPLOAD_DIR / filename

            # parts를 순회하며 텍스트와 이미지 데이터 추출
            image_found = False
            analysis_text = ""

            # 응답 구조 확인
            if hasattr(response, 'parts'):
                print("DEBUG: response.parts exists")
                parts = response.parts
            elif hasattr(response, 'candidates'):
                print("DEBUG: Using response.candidates")
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                    else:
                        raise Exception(f"Unexpected candidate structure: {dir(candidate)}")
                else:
                    raise Exception("No candidates in response")
            else:
                raise Exception(f"Unknown response structure. Attributes: {dir(response)}")

            for part in parts:
                if hasattr(part, 'text') and part.text is not None:
                    # 텍스트 분석 내용 수집
                    analysis_text += part.text
                    print(f"Response text: {part.text[:200]}...")
                elif hasattr(part, 'inline_data') and part.inline_data is not None:
                    # 이미지 데이터 발견
                    print("Image data found in response")
                    print(f"DEBUG: inline_data type: {type(part.inline_data)}")
                    print(f"DEBUG: inline_data attributes: {dir(part.inline_data)}")

                    # inline_data에서 이미지 데이터 추출
                    if hasattr(part.inline_data, 'data'):
                        image_data = part.inline_data.data
                        mime_type = getattr(part.inline_data, 'mime_type', 'image/png')

                        print(f"DEBUG: MIME type: {mime_type}")
                        print(f"DEBUG: Image data length: {len(image_data)}")

                        # base64 디코딩 후 PIL Image로 변환
                        try:
                            image_bytes = base64.b64decode(image_data)
                            image = Image.open(BytesIO(image_bytes))
                            image.save(str(output_path))
                            print(f"Image saved successfully to: {output_path}")
                            image_found = True
                            break
                        except Exception as img_error:
                            print(f"DEBUG: Failed to decode/save image: {img_error}")
                            # base64 디코딩 없이 직접 시도
                            try:
                                image = Image.open(BytesIO(image_data))
                                image.save(str(output_path))
                                print(f"Image saved successfully (without base64 decode) to: {output_path}")
                                image_found = True
                                break
                            except Exception as img_error2:
                                print(f"DEBUG: Failed to save image directly: {img_error2}")
                                raise

            if not image_found:
                raise Exception("Gemini가 이미지를 생성하지 못했습니다. 텍스트 응답만 반환되었습니다.")

            return {
                'filename': filename,
                'analysis': analysis_text.strip() if analysis_text else "분석 내용이 생성되지 않았습니다."
            }

        except Exception as e:
            print(f"Error in generate_interior_image: {type(e).__name__}: {str(e)}")
            raise Exception(f"인테리어 이미지 생성 중 오류 발생: {str(e)}")


# 싱글톤 인스턴스
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """GeminiService 인스턴스 가져오기"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
