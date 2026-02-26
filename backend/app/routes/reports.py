"""
Report routes – generate and download PDF reports.
"""

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.models.schemas import ReportGenerateRequest, ReportResponse
from app.services.ai_service import get_analysis_by_id
from app.services.pdf_service import generate_analysis_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(request: ReportGenerateRequest):
    """
    📄 **Generate PDF Report**

    Create a downloadable PDF report for a completed analysis session.
    The report includes:
    - Session information
    - Summary results with visual bar chart
    - Per-image classification table
    - Notes and disclaimer
    """
    # Fetch the analysis record
    record = await get_analysis_by_id(request.analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {request.analysis_id}",
        )

    try:
        report_path = generate_analysis_report(
            record=record,
            title=request.title or "Acrosome Intactness Analysis Report",
            include_images=request.include_images,
        )

        filename = os.path.basename(report_path)

        return ReportResponse(
            report_id=filename.replace(".pdf", ""),
            analysis_id=request.analysis_id,
            filename=filename,
            download_url=f"/api/reports/download/{filename}",
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.get("/download/{filename}")
async def download_report(filename: str):
    """
    ⬇️ **Download PDF Report**

    Download a previously generated PDF report by filename.
    """
    from app.config import settings
    report_path = os.path.join(settings.REPORTS_DIR, filename)

    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file not found: {filename}",
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
