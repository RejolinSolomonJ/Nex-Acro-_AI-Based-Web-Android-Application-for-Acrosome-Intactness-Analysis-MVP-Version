"""
AI Analysis Service – orchestrates the full analysis pipeline:
  1. Accept multiple uploaded images
  2. Validate each file
  3. Save to disk
  4. Run CNN prediction on each image
  5. Compute aggregate statistics (intact %)
  6. Store results in MongoDB
  7. Return structured response
"""

import os
import time
import uuid
import traceback
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, BackgroundTasks

from app.config import settings
from app.models.analysis import AnalysisRecord, SingleImageResult
from app.ml.predict import predict_single, predict_batch
from app.ml.preprocessing import validate_image_file


async def analyze_images(
    files: list[UploadFile],
    background_tasks: Optional[BackgroundTasks] = None,
    user_id: Optional[str] = None,
    sample_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    age: Optional[int] = None,
    occupation: Optional[str] = None,
    height: Optional[float] = None,
    weight: Optional[float] = None,
    bmi: Optional[float] = None,
    is_alcoholic: bool = False,
    is_smoker: bool = False,
    is_using_drugs: bool = False,
    physical_activity: bool = False,
    has_medical_history: bool = False,
    has_surgical_history: bool = False,
    medical_history_details: Optional[str] = None,
    surgical_history_details: Optional[str] = None,
    sexual_abstinence: Optional[str] = None,
    sexual_lubricants: Optional[str] = None,
    sexual_std_history: Optional[str] = None,
    education: Optional[str] = None,
    address: Optional[str] = None,
    notes: Optional[str] = None,
) -> AnalysisRecord:
    """
    Full analysis pipeline for a batch of uploaded images.
    """
    # ── Idempotency Check ──
    # If a request for the same patient/sample comes in within 60 seconds, 
    # return the existing record instead of re-analysing everything.
    if patient_id and sample_id:
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(seconds=60)
        existing = await AnalysisRecord.find_one(
            AnalysisRecord.patient_id == patient_id,
            AnalysisRecord.patient_name == patient_name,
            AnalysisRecord.sample_id == sample_id,
            AnalysisRecord.created_at >= recent_cutoff
        )
        if existing:
            print(f"[IDEMPOTENT] Reusing recent analysis for {patient_id}/{sample_id}")
            return existing

    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    overall_start = time.perf_counter()

    image_results: list[SingleImageResult] = []
    all_bytes: list[bytes] = []
    file_metadata: list[dict] = []

    # ── Step 1: Validate and read all files ──────────────────
    for file in files:
        content = await file.read()
        file_size = len(content)

        is_valid, error_msg = validate_image_file(file.filename, file_size)
        if not is_valid:
            print(f"[WARN] Skipped invalid file: {file.filename} - {error_msg}")
            continue

        # Generate safe unique filename (no spaces, ASCII-only)
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
        # Treat HEIC/HEIF as JPG since we convert on decode
        if ext in ("heic", "heif"):
            ext = "jpg"
        unique_name = f"{session_id}_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = str(Path(settings.UPLOAD_DIR) / unique_name)

        try:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(content)
            print(f"[OK] Saved: {unique_name} ({file_size} bytes)")
        except Exception as save_err:
            print(f"[ERROR] Could not save {unique_name}: {save_err}")
            traceback.print_exc()
            continue

        all_bytes.append(content)
        file_metadata.append({
            "original_filename": file.filename,
            "saved_filename": unique_name,
            "save_path": save_path,
        })

    if not all_bytes:
        raise ValueError("No valid images were provided for analysis.")

    # ── Step 2: Run batch prediction ─────────────────────────
    try:
        predictions = predict_batch(all_bytes)
    except Exception as pred_err:
        print(f"[ERROR] predict_batch failed: {pred_err}")
        traceback.print_exc()
        raise

    # ── Step 3: Build per-image results ──────────────────────
    for meta, pred in zip(file_metadata, predictions):
        result = SingleImageResult(
            filename=meta["saved_filename"],
            original_filename=meta["original_filename"],
            classification=pred["classification"],
            image_path=meta["save_path"],
            processing_time_ms=pred["processing_time_ms"],
        )
        image_results.append(result)

    # ── Step 4: Compute aggregate stats ──────────────────────
    total = len(image_results)
    intact_count = sum(1 for r in image_results if r.classification == "intact")
    damaged_count = total - intact_count
    intact_pct = round((intact_count / total) * 100, 2) if total > 0 else 0.0
    damaged_pct = round((damaged_count / total) * 100, 2) if total > 0 else 0.0

    total_processing_ms = (time.perf_counter() - overall_start) * 1000

    # ── Step 5: Create and save analysis record ──────────────
    record = AnalysisRecord(
        user_id=user_id,
        session_id=session_id,
        image_results=image_results,
        total_images=total,
        intact_count=intact_count,
        damaged_count=damaged_count,
        intact_percentage=intact_pct,
        damaged_percentage=damaged_pct,
        notes=notes,
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
        total_processing_time_ms=round(total_processing_ms, 2),
    )

    await record.insert()
    print(f"[OK] Analysis saved: {session_id} | {total} images | {intact_pct}% intact")

    # ── Step 6: Pre-generate PDF so download is instant ──────
    if background_tasks:
        from app.services.pdf_service import generate_analysis_report
        
        def safely_generate():
            try:
                generate_analysis_report(record)
                print(f"[OK] PDF pre-generated for {session_id}")
            except Exception as pdf_err:
                print(f"[WARN] PDF pre-generation failed (non-fatal): {pdf_err}")

        background_tasks.add_task(safely_generate)

    return record


async def get_analysis_by_id(analysis_id: str) -> Optional[AnalysisRecord]:
    """Retrieve an analysis record by its MongoDB ID."""
    from beanie import PydanticObjectId
    try:
        record = await AnalysisRecord.get(PydanticObjectId(analysis_id))
        return record
    except Exception:
        return None


async def get_analysis_by_session(session_id: str) -> Optional[AnalysisRecord]:
    """Retrieve an analysis record by session ID."""
    return await AnalysisRecord.find_one(AnalysisRecord.session_id == session_id)


async def list_analyses(
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AnalysisRecord], int]:
    """
    List analysis records with pagination.

    Returns:
        (list_of_records, total_count)
    """
    query = {}
    if user_id:
        query["user_id"] = user_id

    total = await AnalysisRecord.find(query).count()

    records = (
        await AnalysisRecord.find(query)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )

    return records, total


async def delete_analysis(analysis_id: str) -> bool:
    """Delete an analysis record and its associated images."""
    from beanie import PydanticObjectId
    try:
        record = await AnalysisRecord.get(PydanticObjectId(analysis_id))
        if not record:
            return False

        # Delete associated image files
        for result in record.image_results:
            if os.path.exists(result.image_path):
                os.remove(result.image_path)

        await record.delete()
        return True
    except Exception:
        return False
