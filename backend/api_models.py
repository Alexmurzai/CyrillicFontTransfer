"""
Pydantic модели для HFR API.
"""
from pydantic import BaseModel, Field
from typing import Optional


class FontMatch(BaseModel):
    """Один результат поиска шрифта."""
    id: int
    font_name: str
    score: float
    similarity_pct: float = Field(description="Процент сходства (0-100)")
    preview_base64: str = Field(description="Base64-encoded PNG preview")
    font_path: str
    font_category: str = Field(default="unknown", description="serif|sans|script|display|mono|unknown")


class RecognitionResponse(BaseModel):
    """Полный ответ с результатами распознавания."""
    char_images: list[str] = Field(description="Base64 PNG для каждого сегментированного символа")
    matches: list[FontMatch]
    total: int = Field(description="Общее число найденных совпадений")


class HealthResponse(BaseModel):
    """Статус здоровья сервиса."""
    status: str
    engine_loaded: bool
    fonts_count: int
    device: str
