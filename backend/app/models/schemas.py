"""
Pydantic schemas for API request / response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════
# Auth Schemas
# ═══════════════════════════════════════════════════════════════

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


# ═══════════════════════════════════════════════════════════════
# Analysis Schemas
# ═══════════════════════════════════════════════════════════════

class ImageResultResponse(BaseModel):
    filename: str
    original_filename: str
    classification: str
    confidence: float
    processing_time_ms: float


class AnalysisResponse(BaseModel):
    id: str
    session_id: str
    total_images: int
    intact_count: int
    damaged_count: int
    intact_percentage: float
    damaged_percentage: float
    average_confidence: float
    image_results: list[ImageResultResponse]
    sample_id: Optional[str] = None
    patient_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    total_processing_time_ms: float


class AnalysisListItem(BaseModel):
    id: str
    session_id: str
    total_images: int
    intact_percentage: float
    damaged_percentage: float
    average_confidence: float
    sample_id: Optional[str] = None
    patient_id: Optional[str] = None
    created_at: datetime


class AnalysisListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    analyses: list[AnalysisListItem]


# ═══════════════════════════════════════════════════════════════
# Analytics Schemas
# ═══════════════════════════════════════════════════════════════

class AnalyticsSummary(BaseModel):
    total_analyses: int
    total_images_processed: int
    overall_intact_percentage: float
    overall_damaged_percentage: float
    average_confidence: float
    analyses_today: int
    analyses_this_week: int
    analyses_this_month: int


class DailyAnalytics(BaseModel):
    date: str
    analyses_count: int
    images_count: int
    avg_intact_percentage: float


class AnalyticsDetailResponse(BaseModel):
    summary: AnalyticsSummary
    daily_stats: list[DailyAnalytics]


# ═══════════════════════════════════════════════════════════════
# Report Schemas
# ═══════════════════════════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    analysis_id: str
    include_images: bool = False
    title: Optional[str] = "Acrosome Intactness Analysis Report"


class ReportResponse(BaseModel):
    report_id: str
    analysis_id: str
    filename: str
    download_url: str
    generated_at: datetime
