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
from typing import Optional

from fastapi import UploadFile

from app.config import settings
from app.models.analysis import AnalysisRecord, SingleImageResult
from app.ml.predict import predict_single, predict_batch
from app.ml.preprocessing import validate_image_file


async def analyze_images(
    files: list[UploadFile],
    user_id: Optional[str] = None,
    sample_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> AnalysisRecord:
    """
    Full analysis pipeline for a batch of uploaded images.

    Args:
        files: List of uploaded image files
        user_id: ID of the authenticated user (optional)
        sample_id: Lab sample identifier (optional)
        patient_id: Patient identifier (optional)
        notes: Additional notes (optional)

    Returns:
        AnalysisRecord document saved to MongoDB
    """
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
            # Skip invalid files but log the issue
            print(f"⚠️  Skipped invalid file: {file.filename} – {error_msg}")
            continue

        # Generate unique filename
        ext = file.filename.rsplit(".", 1)[-1].lower()
        unique_name = f"{session_id}_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        # Save to disk
        with open(save_path, "wb") as f:
            f.write(content)

        all_bytes.append(content)
        file_metadata.append({
            "original_filename": file.filename,
            "saved_filename": unique_name,
            "save_path": save_path,
        })

    if not all_bytes:
        raise ValueError("No valid images were provided for analysis.")

    # ── Step 2: Run batch prediction ─────────────────────────
    predictions = predict_batch(all_bytes)

    # ── Step 3: Build per-image results ──────────────────────
    for meta, pred in zip(file_metadata, predictions):
        result = SingleImageResult(
            filename=meta["saved_filename"],
            original_filename=meta["original_filename"],
            classification=pred["classification"],
            confidence=pred["confidence"],
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
    avg_confidence = round(
        sum(r.confidence for r in image_results) / total, 4
    ) if total > 0 else 0.0

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
        average_confidence=avg_confidence,
        notes=notes,
        sample_id=sample_id,
        patient_id=patient_id,
        total_processing_time_ms=round(total_processing_ms, 2),
    )

    await record.insert()
    print(f"✅  Analysis saved: {session_id} | {total} images | {intact_pct}% intact")

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
