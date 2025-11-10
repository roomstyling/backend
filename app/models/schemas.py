from pydantic import BaseModel
from typing import Optional, List


class StyleOption(BaseModel):
    """인테리어 스타일 옵션"""
    id: str
    name: str
    description: str


class RoomAnalysis(BaseModel):
    """원룸 분석 결과"""
    room_type: str
    size_estimate: str
    current_layout: str
    issues: List[str]
    strengths: List[str]


class DesignGuide(BaseModel):
    """인테리어 디자인 가이드"""
    style: str
    analysis: RoomAnalysis
    recommendations: List[str]
    layout_suggestions: str
    color_scheme: str
    furniture_suggestions: List[str]


class DesignRequest(BaseModel):
    """디자인 요청"""
    image_filename: str
    style_id: str


class DesignResponse(BaseModel):
    """디자인 응답"""
    success: bool
    message: str
    guide: Optional[DesignGuide] = None
