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

            # 이미지 편집 프롬프트 (보수적 접근, 구조 보존 강조)
            prompt = f"""
You are a professional interior designer with 15+ years of experience in {style} style design.

CRITICAL CONSTRAINT: This is a SUBTLE RENOVATION, not a complete rebuild. Keep the room's existing structure and layout EXACTLY as is.

TASK: Analyze this room and apply MINIMAL {style} style changes while preserving the existing layout.

STEP 1 - ANALYSIS (Please describe in your response):
Analyze and document:
- Current room dimensions and layout
- Exact window positions, door locations, and their sizes
- Existing furniture placement and types
- Current color scheme and materials
- Natural lighting conditions
- What's already working well in this space

STEP 2 - {style} STYLE APPLICATION (Please describe your changes):
Style Description: {style_description}

Apply ONLY these conservative changes:
1. WALL COLORS: Change wall paint to {style}-appropriate colors
2. FURNITURE STYLING: Keep existing furniture POSITIONS, but change:
   - Furniture materials/finishes to match {style}
   - Upholstery colors/patterns to {style} palette
3. SOFT FURNISHINGS: Update curtains, rugs, cushions, bedding to {style}
4. LIGHTING FIXTURES: Replace light fixtures with {style}-appropriate designs (keep positions)
5. DECORATIVE ACCENTS: Add {style} artwork, plants, and small decorative items
6. FLOORING: Update flooring material to match {style} (wood/tile style)

STRICT PRESERVATION RULES - DO NOT CHANGE:
❌ Room dimensions or walls
❌ Window sizes or positions
❌ Door sizes or positions
❌ Ceiling height or structure
❌ Overall furniture layout (bed, desk, shelf positions)
❌ Major architectural features

EXECUTION REQUIREMENTS:
✓ The "before" and "after" should have the SAME room layout
✓ Someone should immediately recognize this as the same room
✓ Changes should feel realistic and achievable with normal renovation
✓ Focus on surface-level styling: colors, materials, decorations
✓ Create a photorealistic result
✓ The transformation should look professional but CONSERVATIVE

RESPONSE FORMAT:
First, provide your analysis and design decisions in text.
Then, generate the transformed image.

Explain:
- What you observed about the current room
- Specific changes you're making and why
- How these changes achieve the {style} aesthetic while respecting the existing structure
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
