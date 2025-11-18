import os
import google.generativeai as genai_old
from google import genai
from google.genai import types
from google.generativeai.types import content_types
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

        # Structured Output 스키마 정의
        self._setup_schemas()

    def _setup_schemas(self):
        """Structured Output용 JSON 스키마 정의"""
        # 방 분석 스키마
        self.room_analysis_schema = content_types.to_content({
            "type": "object",
            "properties": {
                "room_type": {"type": "string", "description": "원룸/투룸 등 방 타입"},
                "size_estimate": {"type": "string", "description": "평수 추정"},
                "current_layout": {"type": "string", "description": "현재 레이아웃 설명"},
                "issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "문제점 목록"
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "장점 목록"
                }
            },
            "required": ["room_type", "size_estimate", "current_layout", "issues", "strengths"]
        })

        # 디자인 가이드 스키마
        self.design_guide_schema = content_types.to_content({
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "추천사항 목록"
                },
                "layout_suggestions": {"type": "string", "description": "레이아웃 제안 상세 설명"},
                "color_scheme": {"type": "string", "description": "색상 배치 제안"},
                "furniture_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "가구 제안 목록"
                }
            },
            "required": ["recommendations", "layout_suggestions", "color_scheme", "furniture_suggestions"]
        })

    async def analyze_room(self, image_path: str) -> Dict[str, Any]:
        """원룸 사진 분석 (Structured Output 사용)"""
        try:
            img = Image.open(image_path)

            prompt = """
            이 원룸 사진을 분석해주세요.

            특히 다음 사항을 확인해주세요:
            - room_type: 원룸/투룸 등 방 타입
            - size_estimate: 평수 추정
            - current_layout: 현재 레이아웃 설명
            - issues: 방문 옆 침대 여부(동선), 채광, 공간 활용도, 수납, 가구 배치 문제점
            - strengths: 장점 목록
            """

            # Structured Output 사용
            response = self.model.generate_content(
                [prompt, img],
                generation_config=genai_old.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=self.room_analysis_schema
                )
            )

            # JSON 자동 파싱 (Structured Output은 항상 유효한 JSON 반환)
            return json.loads(response.text)

        except Exception as e:
            raise Exception(f"이미지 분석 중 오류 발생: {str(e)}")

    async def generate_design_guide(
        self,
        image_path: str,
        analysis: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """인테리어 디자인 가이드 생성 (Structured Output 사용)"""
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

            다음 항목을 포함해주세요:
            - recommendations: 추천사항 목록
            - layout_suggestions: 동선을 고려한 레이아웃 제안 상세 설명
            - color_scheme: 스타일에 맞는 색상 배치 제안
            - furniture_suggestions: 공간 최적화 및 수납을 위한 가구 제안 목록
            """

            # Structured Output 사용
            response = self.model.generate_content(
                [prompt, img],
                generation_config=genai_old.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=self.design_guide_schema
                )
            )

            # JSON 자동 파싱 (Structured Output은 항상 유효한 JSON 반환)
            return json.loads(response.text)

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

            # 전문 인테리어 디자이너 프롬프트
            prompt = f"""
You are an award-winning interior designer with 15+ years of experience specializing in residential spaces.
You've completed over 500 successful room transformations and are known for your ability to see potential in every space.

=== YOUR MISSION ===
Transform this room with {style} style while respecting its unique character.

{style} 스타일의 본질: {style_info['essence']}
디자인 철학: {style_info['approach']}

=== YOUR DESIGN PROCESS ===

First, study this room like you're meeting a new client. Look deeply:
- What makes this space special? What's already working well?
- What's holding it back? Where's the friction in daily life?
- How does the light move through the space? What's the flow?
- If you lived here, what would frustrate you? What would delight you?

Then, envision the transformation:
- How can {style} style solve the real problems here?
- What elements should stay because they're perfect as-is?
- What small changes would make the biggest impact?
- Where can you add personality without overcrowding?
- How to make this feel authentically {style}, not like a magazine copy?

=== DESIGN GUIDELINES (your creative intuition, not rigid rules) ===

Respect what works:
The best designers know when to leave things alone. If the natural light is beautiful, enhance it. If there's a good furniture piece, work with it. Don't change for change's sake.

Solve real problems:
Bad lighting? Fix it. Awkward flow? Rearrange. Cluttered? Simplify. Each change should have a purpose.

Add {style} authentically:
This isn't about checking boxes (white walls = minimalist). It's about capturing the feeling. What makes {style} spaces feel the way they do? That's what you're after.

Stay grounded in reality:
This room needs to work for real life. Beautiful but livable. Stylish but comfortable. Instagram-worthy but actually functional.

=== YOUR DELIVERABLE (한국어로 작성) ===

전문가 분석:

1. 원본 공간의 가능성
   - 이 공간만의 매력 포인트 (반드시 살려야 할 것)
   - 현재 방해 요소 (개선이 필요한 부분)
   - 전반적인 공간 느낌과 잠재력

2. {style} 스타일 디자인 제안
   - 핵심 변화: 가장 임팩트 있는 3가지 개선사항
   - 색감과 소재: 어떤 톤과 질감으로 {style} 감성을 담을지
   - 디테일: 작지만 중요한 터치 (조명, 소품, 텍스처 등)
   - 추가/변경 가구 (필요한 경우만, 구체적인 이유와 함께)

3. 디자이너의 한 마디
   - 이 디자인이 거주자의 삶을 어떻게 개선할지

Now, generate the transformed image that brings this vision to life.
Make it feel lived-in, not staged. Real, not fake. {style}, not stereotypical.
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
