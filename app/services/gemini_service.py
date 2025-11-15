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
    ) -> Optional[str]:
        """인테리어 스타일이 적용된 이미지 생성 (Gemini 2.5 Flash Image 사용)

        Returns:
            생성된 이미지의 파일명
        """
        try:
            # 원본 이미지 로드
            original_image = Image.open(image_path)

            # 이미지 편집 프롬프트
            prompt = f"""
            Transform this room into a {style} style interior design.

            Style description: {style_description}

            Requirements:
            - Keep the room structure (windows, doors, walls) but redesign the interior
            - Apply {style} style furniture arrangement
            - Use {style} style color palette
            - Add appropriate lighting and decorative items
            - Make it realistic and practical
            - Maximize space utilization
            - Create a high-quality, photorealistic interior rendering

            Make it look professional and inviting while maintaining the original room layout.
            """

            print(f"Generating image with prompt: {prompt[:150]}...")

            # Gemini 2.5 Flash Image로 이미지 편집
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, original_image],
            )

            # 응답에서 이미지 데이터 추출 및 저장
            import uuid
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            UPLOAD_DIR = BASE_DIR / "uploads"
            UPLOAD_DIR.mkdir(exist_ok=True)

            filename = f"generated_{uuid.uuid4()}.png"
            output_path = UPLOAD_DIR / filename

            # parts를 순회하며 이미지 데이터 찾기
            image_found = False
            for part in response.parts:
                if part.text is not None:
                    print(f"Response text: {part.text[:200]}...")
                elif part.inline_data is not None:
                    # 이미지 데이터 발견
                    print("Image data found in response")
                    image = part.as_image()
                    image.save(str(output_path))
                    print(f"Image saved successfully to: {output_path}")
                    image_found = True
                    break

            if not image_found:
                raise Exception("Gemini가 이미지를 생성하지 못했습니다. 텍스트 응답만 반환되었습니다.")

            return filename

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
