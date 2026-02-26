"""
Analytics routes – summary statistics for the admin dashboard.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter

from app.models.analysis import AnalysisRecord
from app.models.schemas import AnalyticsSummary, AnalyticsDetailResponse, DailyAnalytics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary_analytics():
    """
    📊 **Get Summary Analytics**

    Returns aggregate statistics across all analyses:
    - Total analyses & images processed
    - Overall intact/damaged percentages
    - Average model confidence
    - Counts for today / this week / this month
    """
    all_records = await AnalysisRecord.find_all().to_list()

    total_analyses = len(all_records)
    total_images = sum(r.total_images for r in all_records)

    if total_analyses > 0:
        total_intact = sum(r.intact_count for r in all_records)
        total_damaged = sum(r.damaged_count for r in all_records)
        overall_intact_pct = round((total_intact / total_images) * 100, 2) if total_images > 0 else 0
        overall_damaged_pct = round((total_damaged / total_images) * 100, 2) if total_images > 0 else 0
        avg_confidence = round(
            sum(r.average_confidence for r in all_records) / total_analyses, 4
        )
    else:
        overall_intact_pct = 0.0
        overall_damaged_pct = 0.0
        avg_confidence = 0.0

    # Time-based counts
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    analyses_today = sum(1 for r in all_records if r.created_at >= today_start)
    analyses_week = sum(1 for r in all_records if r.created_at >= week_start)
    analyses_month = sum(1 for r in all_records if r.created_at >= month_start)

    return AnalyticsSummary(
        total_analyses=total_analyses,
        total_images_processed=total_images,
        overall_intact_percentage=overall_intact_pct,
        overall_damaged_percentage=overall_damaged_pct,
        average_confidence=avg_confidence,
        analyses_today=analyses_today,
        analyses_this_week=analyses_week,
        analyses_this_month=analyses_month,
    )


@router.get("/detailed", response_model=AnalyticsDetailResponse)
async def get_detailed_analytics(days: int = 30):
    """
    📊 **Get Detailed Analytics with Daily Breakdown**

    Returns the summary stats plus a day-by-day breakdown
    for the last N days (default: 30).
    """
    summary = await get_summary_analytics()

    # Daily breakdown
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    records = await AnalysisRecord.find(
        AnalysisRecord.created_at >= start_date
    ).to_list()

    # Group by date
    daily_map: dict[str, dict] = {}
    for r in records:
        date_str = r.created_at.strftime("%Y-%m-%d")
        if date_str not in daily_map:
            daily_map[date_str] = {
                "analyses_count": 0,
                "images_count": 0,
                "intact_total": 0.0,
            }
        daily_map[date_str]["analyses_count"] += 1
        daily_map[date_str]["images_count"] += r.total_images
        daily_map[date_str]["intact_total"] += r.intact_percentage

    daily_stats = []
    for date_str in sorted(daily_map.keys()):
        data = daily_map[date_str]
        avg_intact = round(data["intact_total"] / data["analyses_count"], 2)
        daily_stats.append(DailyAnalytics(
            date=date_str,
            analyses_count=data["analyses_count"],
            images_count=data["images_count"],
            avg_intact_percentage=avg_intact,
        ))

    return AnalyticsDetailResponse(
        summary=summary,
        daily_stats=daily_stats,
    )
