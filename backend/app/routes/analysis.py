"""
Analysis routes – upload images, get results, list analyses.
This is the core endpoint for the acrosome intactness analysis.
"""

from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, BackgroundTasks

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
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="One or more microscope images to analyze"),
    sample_id: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    patient_name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    education: Optional[str] = Form(None),
    occupation: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    height: Optional[float] = Form(None),
    weight: Optional[float] = Form(None),
    bmi: Optional[float] = Form(None),
    is_alcoholic: bool = Form(False),
    is_smoker: bool = Form(False),
    is_using_drugs: bool = Form(False),
    physical_activity: bool = Form(False),
    has_medical_history: bool = Form(False),
    has_surgical_history: bool = Form(False),
    medical_history_details: Optional[str] = Form(None),
    surgical_history_details: Optional[str] = Form(None),
    sexual_abstinence: Optional[str] = Form(None),
    sexual_lubricants: Optional[str] = Form(None),
    sexual_std_history: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
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
            background_tasks=background_tasks,
            user_id=user_id,
            sample_id=sample_id,
            patient_id=patient_id,
            patient_name=patient_name,
            age=age,
            education=education,
            occupation=occupation,
            address=address,
            height=height,
            weight=weight,
            bmi=bmi,
            is_alcoholic=is_alcoholic,
            is_smoker=is_smoker,
            is_using_drugs=is_using_drugs,
            physical_activity=physical_activity,
            has_medical_history=has_medical_history,
            has_surgical_history=has_surgical_history,
            medical_history_details=medical_history_details,
            surgical_history_details=surgical_history_details,
            sexual_abstinence=sexual_abstinence,
            sexual_lubricants=sexual_lubricants,
            sexual_std_history=sexual_std_history,
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
            image_results=[
                ImageResultResponse(
                    filename=r.filename,
                    original_filename=r.original_filename,
                    classification=r.classification,
                    processing_time_ms=r.processing_time_ms,
                )
                for r in record.image_results
            ],
            sample_id=record.sample_id,
            patient_id=record.patient_id,
            patient_name=record.patient_name,
            age=record.age,
            education=record.education,
            occupation=record.occupation,
            address=record.address,
            height=record.height,
            weight=record.weight,
            bmi=record.bmi,
            is_alcoholic=record.is_alcoholic,
            is_smoker=record.is_smoker,
            is_using_drugs=record.is_using_drugs,
            physical_activity=record.physical_activity,
            has_medical_history=record.has_medical_history,
            has_surgical_history=record.has_surgical_history,
            medical_history_details=record.medical_history_details,
            surgical_history_details=record.surgical_history_details,
            sexual_abstinence=record.sexual_abstinence,
            sexual_lubricants=record.sexual_lubricants,
            sexual_std_history=record.sexual_std_history,
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
        image_results=[
            ImageResultResponse(
                filename=r.filename,
                original_filename=r.original_filename,
                classification=r.classification,
                processing_time_ms=r.processing_time_ms,
            )
            for r in record.image_results
        ],
        sample_id=record.sample_id,
        patient_id=record.patient_id,
        patient_name=record.patient_name,
        age=record.age,
        occupation=record.occupation,
        height=record.height,
        weight=record.weight,
        bmi=record.bmi,
        is_alcoholic=record.is_alcoholic,
        is_smoker=record.is_smoker,
        is_using_drugs=record.is_using_drugs,
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
        image_results=[
            ImageResultResponse(
                filename=r.filename,
                original_filename=r.original_filename,
                classification=r.classification,
                processing_time_ms=r.processing_time_ms,
            )
            for r in record.image_results
        ],
        sample_id=record.sample_id,
        patient_id=record.patient_id,
        patient_name=record.patient_name,
        age=record.age,
        occupation=record.occupation,
        height=record.height,
        weight=record.weight,
        bmi=record.bmi,
        is_alcoholic=record.is_alcoholic,
        is_smoker=record.is_smoker,
        is_using_drugs=record.is_using_drugs,
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
                sample_id=r.sample_id,
                patient_id=r.patient_id,
                patient_name=r.patient_name,
                age=r.age,
                education=r.education,
                occupation=r.occupation,
                address=r.address,
                height=r.height,
                weight=r.weight,
                bmi=r.bmi,
                is_alcoholic=r.is_alcoholic,
                is_smoker=r.is_smoker,
                is_using_drugs=r.is_using_drugs,
                physical_activity=r.physical_activity,
                has_medical_history=r.has_medical_history,
                has_surgical_history=r.has_surgical_history,
                medical_history_details=r.medical_history_details,
                surgical_history_details=r.surgical_history_details,
                sexual_abstinence=r.sexual_abstinence,
                sexual_lubricants=r.sexual_lubricants,
                sexual_std_history=r.sexual_std_history,
                notes=r.notes,
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
