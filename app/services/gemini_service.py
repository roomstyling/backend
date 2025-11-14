import os
import google.generativeai as genai
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

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

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
        """인테리어 스타일이 적용된 이미지 생성

        Returns:
            생성된 이미지의 파일 경로
        """
        try:
            img = Image.open(image_path)

            # 이미지 생성 프롬프트
            prompt = f"""
            이 원룸 사진을 {style} 스타일로 인테리어 디자인을 적용한 이미지를 생성해주세요.

            스타일 설명: {style_description}

            요구사항:
            1. 원본 방의 구조(창문, 문, 벽)는 유지
            2. {style} 스타일에 맞는 가구 배치
            3. {style} 스타일의 색상 팔레트 적용
            4. 조명과 소품을 스타일에 맞게 추가
            5. 현실적이고 실용적인 인테리어
            6. 공간 활용도를 최대화

            고품질의 사실적인 인테리어 렌더링 이미지를 생성해주세요.
            """

            response = self.model.generate_content([prompt, img])

            print(f"DEBUG: Response type: {type(response)}")
            print(f"DEBUG: Has candidates: {hasattr(response, 'candidates')}")

            # 생성된 이미지 저장
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                print(f"DEBUG: Candidate type: {type(candidate)}")
                print(f"DEBUG: Has content: {hasattr(candidate, 'content')}")

                # 이미지 데이터 추출
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    print(f"DEBUG: Number of parts: {len(candidate.content.parts)}")

                    for i, part in enumerate(candidate.content.parts):
                        print(f"DEBUG: Part {i} type: {type(part)}")
                        print(f"DEBUG: Part {i} has inline_data: {hasattr(part, 'inline_data')}")
                        print(f"DEBUG: Part {i} has text: {hasattr(part, 'text')}")

                        # inline_data가 있는 경우 (이미지)
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                            mime_type = part.inline_data.mime_type
                            print(f"DEBUG: Found image data, MIME type: {mime_type}")
                            print(f"DEBUG: Image data length: {len(image_data)}")

                            # base64 디코딩
                            try:
                                image_bytes = base64.b64decode(image_data)
                                print(f"DEBUG: Decoded image bytes length: {len(image_bytes)}")
                            except Exception as decode_error:
                                print(f"DEBUG: Base64 decode error: {decode_error}")
                                raise

                            # 이미지 저장 (절대 경로 사용)
                            import uuid
                            BASE_DIR = Path(__file__).resolve().parent.parent.parent
                            UPLOAD_DIR = BASE_DIR / "uploads"
                            UPLOAD_DIR.mkdir(exist_ok=True)

                            filename = f"generated_{uuid.uuid4()}.png"
                            output_path = UPLOAD_DIR / filename
                            print(f"DEBUG: Saving to: {output_path}")

                            with open(str(output_path), "wb") as f:
                                f.write(image_bytes)

                            print(f"DEBUG: File saved successfully")
                            return filename

                        # 텍스트가 있는 경우
                        if hasattr(part, 'text'):
                            print(f"DEBUG: Part {i} text preview: {part.text[:200]}...")

                # 텍스트 응답만 있는 경우
                raise Exception("이미지가 생성되지 않았습니다. 모델이 텍스트만 반환했습니다.")

            raise Exception("이미지 생성 실패: 응답이 없습니다.")

        except Exception as e:
            print(f"DEBUG: Exception occurred: {type(e).__name__}: {str(e)}")
            raise Exception(f"인테리어 이미지 생성 중 오류 발생: {str(e)}")


# 싱글톤 인스턴스
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """GeminiService 인스턴스 가져오기"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
