# Pydantic modelleri, API istekleri ve yanıtları için veri yapılarını tanımlar.
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class DemandLevel(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class TrendDirection(str, Enum):
    RISING = "rising"
    STABLE = "stable"
    FALLING = "falling"
    VOLATILE = "volatile"


class AnalizRequest(BaseModel):
    konu: str = Field(..., min_length=1, max_length=100)


class TimingInfo(BaseModel):
    google_trends_seconds: float
    data_processing_seconds: float
    ai_request_seconds: float
    response_processing_seconds: float
    total_seconds: float


class AnalizResponse(BaseModel):
    konu: str
    opportunity_score: int = Field(..., ge=0, le=100)
    demand_level: DemandLevel
    trend_direction: TrendDirection
    summary: str = Field(..., max_length=200)  # kısa fırsat özeti
    key_reasons: List[str] = Field(..., min_length=2, max_length=3)
    opportunities: List[str] = Field(..., min_length=2, max_length=3)
    risks: List[str] = Field(..., min_length=1, max_length=3)
    timing: TimingInfo
