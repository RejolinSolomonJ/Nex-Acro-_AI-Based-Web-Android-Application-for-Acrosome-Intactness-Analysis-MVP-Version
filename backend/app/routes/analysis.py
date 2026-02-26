"""
Analysis routes – upload images, get results, list analyses.
This is the core endpoint for the acrosome intactness analysis.
"""

from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status

from app.models.user import User
from app.models.schemas import (
    AnalysisResponse,
    ImageResultResponse,
    AnalysisListResponse,
    AnalysisListItem,
)
from app.services.ai_service import (
    analyze_images,
    get_analysis_by_id,
    get_analysis_by_session,
    list_analyses,
    delete_analysis,
)
from app.utils.security import get_current_user
from app.ml.predict import get_model_info

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_analyze(
    files: list[UploadFile] = File(..., description="One or more microscope images to analyze"),
    sample_id: Optional[str] = Form(None, description="Lab sample identifier"),
    patient_id: Optional[str] = Form(None, description="Patient identifier"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    user: Optional[User] = Depends(get_current_user),
):
    """
    🔬 **Analyze Acrosome Intactness**

    Upload one or more microscope images of sperm samples.
    The AI model will classify each image as **Intact** or **Damaged**
    and return the overall **intact percentage**.

    **Supported formats:** JPG, JPEG, PNG, BMP, TIFF

    **Returns:**
    - Per-image classification with confidence scores
    - Overall intact/damaged percentages
    - Processing time statistics
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image file is required.",
        )

    # Limit batch size
    if len(files) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 images per batch.",
        )

    try:
        user_id = str(user.id) if user else None

        record = await analyze_images(
            files=files,
            user_id=user_id,
            sample_id=sample_id,
            patient_id=patient_id,
            notes=notes,
        )

        return AnalysisResponse(
            id=str(record.id),
            session_id=record.session_id,
            total_images=record.total_images,
            intact_count=record.intact_count,
            damaged_count=record.damaged_count,
            intact_percentage=record.intact_percentage,
            damaged_percentage=record.damaged_percentage,
            average_confidence=record.average_confidence,
            image_results=[
                ImageResultResponse(
                    filename=r.filename,
                    original_filename=r.original_filename,
                    classification=r.classification,
                    confidence=r.confidence,
                    processing_time_ms=r.processing_time_ms,
                )
                for r in record.image_results
            ],
            sample_id=record.sample_id,
            patient_id=record.patient_id,
            notes=record.notes,
            created_at=record.created_at,
            total_processing_time_ms=record.total_processing_time_ms,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.get("/result/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(analysis_id: str):
    """
    Get the results of a previous analysis by ID.
    """
    record = await get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {analysis_id}",
        )

    return AnalysisResponse(
        id=str(record.id),
        session_id=record.session_id,
        total_images=record.total_images,
        intact_count=record.intact_count,
        damaged_count=record.damaged_count,
        intact_percentage=record.intact_percentage,
        damaged_percentage=record.damaged_percentage,
        average_confidence=record.average_confidence,
        image_results=[
            ImageResultResponse(
                filename=r.filename,
                original_filename=r.original_filename,
                classification=r.classification,
                confidence=r.confidence,
                processing_time_ms=r.processing_time_ms,
            )
            for r in record.image_results
        ],
        sample_id=record.sample_id,
        patient_id=record.patient_id,
        notes=record.notes,
        created_at=record.created_at,
        total_processing_time_ms=record.total_processing_time_ms,
    )


@router.get("/session/{session_id}", response_model=AnalysisResponse)
async def get_analysis_by_session_id(session_id: str):
    """Get analysis results by session ID."""
    record = await get_analysis_by_session(session_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    return AnalysisResponse(
        id=str(record.id),
        session_id=record.session_id,
        total_images=record.total_images,
        intact_count=record.intact_count,
        damaged_count=record.damaged_count,
        intact_percentage=record.intact_percentage,
        damaged_percentage=record.damaged_percentage,
        average_confidence=record.average_confidence,
        image_results=[
            ImageResultResponse(
                filename=r.filename,
                original_filename=r.original_filename,
                classification=r.classification,
                confidence=r.confidence,
                processing_time_ms=r.processing_time_ms,
            )
            for r in record.image_results
        ],
        sample_id=record.sample_id,
        patient_id=record.patient_id,
        notes=record.notes,
        created_at=record.created_at,
        total_processing_time_ms=record.total_processing_time_ms,
    )


@router.get("/list", response_model=AnalysisListResponse)
async def list_all_analyses(
    page: int = 1,
    page_size: int = 20,
    user: Optional[User] = Depends(get_current_user),
):
    """
    List all analysis records with pagination.
    If authenticated, returns only the user's analyses.
    """
    user_id = str(user.id) if user else None
    records, total = await list_analyses(user_id=user_id, page=page, page_size=page_size)

    return AnalysisListResponse(
        total=total,
        page=page,
        page_size=page_size,
        analyses=[
            AnalysisListItem(
                id=str(r.id),
                session_id=r.session_id,
                total_images=r.total_images,
                intact_percentage=r.intact_percentage,
                damaged_percentage=r.damaged_percentage,
                average_confidence=r.average_confidence,
                sample_id=r.sample_id,
                patient_id=r.patient_id,
                created_at=r.created_at,
            )
            for r in records
        ],
    )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_record(analysis_id: str):
    """Delete an analysis record and its associated images."""
    deleted = await delete_analysis(analysis_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {analysis_id}",
        )


@router.get("/model-info")
async def model_info():
    """Get information about the currently loaded AI model."""
    return get_model_info()
