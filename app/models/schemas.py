# Pydantic modelleri, API istekleri ve yanıtları için veri yapılarını tanımlar.
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

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
    konu: str

class AnalizResponse(BaseModel):
    konu: str
    opportunity_score: int  # 0-100
    demand_level: DemandLevel
    trend_direction: TrendDirection
    summary: str  # short opportunity summary
    key_reasons: List[str]  # 2-3 reasons
    opportunities: List[str]  # 2-3 opportunity ideas
    risks: List[str]  # potential risks
    timing: dict  # performance metrics