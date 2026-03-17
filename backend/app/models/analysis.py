"""
Analysis record document model for MongoDB (Beanie ODM).
Stores the results of each acrosome intactness analysis session.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field


class SingleImageResult(BaseModel):
    """Result for one image in the batch."""

    filename: str
    original_filename: str
    classification: str  # "intact" | "damaged"
    image_path: str
    processing_time_ms: float


class AnalysisRecord(Document):
    """
    One analysis session – the user uploads N images,
    each is classified, and an overall intact % is produced.
    """

    user_id: Optional[str] = None
    session_id: str = Field(..., description="Unique session identifier")

    # ── Per-image results ────────────────────────────────────
    image_results: list[SingleImageResult] = []

    # ── Aggregate stats ──────────────────────────────────────
    total_images: int = 0
    intact_count: int = 0
    damaged_count: int = 0
    intact_percentage: float = 0.0
    damaged_percentage: float = 0.0

    # ── Metadata ─────────────────────────────────────────────
    notes: Optional[str] = None
    sample_id: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    
    # ── Patient Context ──────────────────────────────────────
    age: Optional[int] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    is_alcoholic: Optional[bool] = False
    is_smoker: Optional[bool] = False
    is_using_drugs: Optional[bool] = False
    physical_activity: Optional[bool] = False
    has_medical_history: Optional[bool] = False
    medical_history_details: Optional[str] = None
    has_surgical_history: Optional[bool] = False
    surgical_history_details: Optional[str] = None
    sexual_abstinence: Optional[str] = None
    sexual_lubricants: Optional[str] = None
    sexual_std_history: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_processing_time_ms: float = 0.0

    class Settings:
        name = "analyses"
        indexes = ["session_id", "user_id", "created_at"]

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "total_images": 10,
                "intact_count": 7,
                "damaged_count": 3,
                "intact_percentage": 70.0,
                "damaged_percentage": 30.0,
            }
        }
