import os
import google.generativeai as genai_old
from google import genai
from google.genai import types
from PIL import Image
from typing import Dict, Any, Optional
import json
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

            # 스타일별 핵심 원칙 (참고용, 강제 아님)
            style_principles = {
                "미니멀리스트": "심플함, 필수 요소만, 여백 강조, 깔끔한 라인",
                "스칸디나비안": "밝은 원목, 자연스러움, 아늑함, 따뜻한 조명, 식물",
                "모던": "현대적, 세련됨, 기하학적, 중성 색상, 금속 포인트",
                "빈티지": "앤티크, 따뜻함, 복고풍, 장식적 디테일, 낭만적",
                "인더스트리얼": "원자재 노출, 거친 질감, 금속/콘크리트, 산업적 느낌"
            }

            style_principle = style_principles.get(style, style_description)

            # 원본 기반 개선 프롬프트
            prompt = f"""
You are a professional interior designer. Analyze this room and improve it with {style} style.

CRITICAL WORKFLOW:

STEP 1: ANALYZE THE CURRENT ROOM (원본 사진 분석)
Look at THIS specific room and identify:
- What is GOOD and should be KEPT (좋은 점 - 유지할 것)
- What NEEDS IMPROVEMENT (개선이 필요한 점)
- Current colors, furniture, layout, lighting
- Problems: clutter, poor lighting, bad furniture placement, etc.

STEP 2: APPLY {style} IMPROVEMENTS (개선점에만 {style} 스타일 적용)
{style} Style Principle: {style_principle}
{style} Description: {style_description}

IMPORTANT RULES:
✅ KEEP what's already good in the original room
✅ IMPROVE only what needs fixing
✅ Apply {style} style to improvements, not blindly to everything
✅ Respect the original room's character and strengths

PRESERVE:
- Room structure (walls, windows, doors)
- Overall layout
- Elements that already work well

IMPROVE with {style} style:
- Fix problem areas identified in Step 1
- Update materials/finishes where needed
- Add furniture if there are gaps in functionality
- Adjust colors only if current ones clash or look bad
- Improve lighting if insufficient
- Add {style}-appropriate decor if room feels empty

DON'T:
❌ Change colors just because style guide says so - only if current colors are problematic
❌ Replace furniture that already fits the style
❌ Add unnecessary items
❌ Ignore what's already working in the original

OUTPUT (한국어로):
1. 현재 방 분석:
   - 잘되어 있는 점 (유지할 부분)
   - 개선이 필요한 점

2. {style} 스타일 개선 내용:
   - 구체적으로 무엇을 어떻게 바꿨는지
   - 추가한 가구/소품 (있다면)
   - 왜 이렇게 바꿨는지

3. GENERATE THE IMPROVED IMAGE
   - Keep good elements from original
   - Fix problems with {style} style
   - Natural, realistic improvement
            """

            print(f"Generating image with prompt: {prompt[:150]}...")

            # Gemini 3 Pro Image로 이미지 편집
            aspect_ratio = "16:9"
            response = self.client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image'],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                    tools=[{"google_search": {}}]
                )
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

            for part in response.parts:
                if part.text is not None:
                    # 텍스트 분석 내용 수집
                    analysis_text += part.text
                    print(f"Response text: {part.text[:200]}...")
                elif image := part.as_image():
                    # 이미지 데이터 발견
                    print("Image data found in response")
                    image.save(str(output_path))
                    print(f"Image saved successfully to: {output_path}")
                    image_found = True

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
