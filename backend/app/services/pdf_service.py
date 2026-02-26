"""
PDF Report Generation Service.

Generates professional PDF reports for acrosome intactness analysis results.
Uses fpdf2 for PDF creation.
"""

import os
import uuid
from datetime import datetime

from fpdf import FPDF

from app.config import settings
from app.models.analysis import AnalysisRecord


class AcrosomeReport(FPDF):
    """Custom PDF class with header and footer."""

    def __init__(self, title: str = "Acrosome Intactness Analysis Report"):
        super().__init__()
        self.report_title = title

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(25, 60, 120)
        self.cell(0, 10, self.report_title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(25, 60, 120)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(
            0, 10,
            f"Page {self.page_no()}/{{nb}} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Acrosome AI",
            align="C",
        )


def generate_analysis_report(
    record: AnalysisRecord,
    title: str = "Acrosome Intactness Analysis Report",
    include_images: bool = False,
) -> str:
    """
    Generate a PDF report for an analysis session.

    Args:
        record: The AnalysisRecord from MongoDB
        title: Report title
        include_images: Whether to embed sample images

    Returns:
        Path to the generated PDF file
    """
    pdf = AcrosomeReport(title)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ══════════════════════════════════════════════════════════
    # Section 1: Session Information
    # ══════════════════════════════════════════════════════════
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 8, "1. Session Information", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)

    info_data = [
        ("Session ID", record.session_id),
        ("Date & Time", record.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
        ("Sample ID", record.sample_id or "N/A"),
        ("Patient ID", record.patient_id or "N/A"),
        ("Total Images", str(record.total_images)),
        ("Processing Time", f"{record.total_processing_time_ms:.0f} ms"),
    ]

    for label, value in info_data:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(50, 7, f"{label}:", new_x="END")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # ══════════════════════════════════════════════════════════
    # Section 2: Summary Results (with visual bar)
    # ══════════════════════════════════════════════════════════
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 8, "2. Analysis Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Intact percentage - big display
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(34, 139, 34)  # Green
    pdf.cell(0, 15, f"{record.intact_percentage:.1f}% Intact", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(200, 50, 50)  # Red
    pdf.cell(0, 10, f"{record.damaged_percentage:.1f}% Damaged", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Visual progress bar
    bar_x = 30
    bar_y = pdf.get_y()
    bar_width = 150
    bar_height = 12

    # Background (damaged – red)
    pdf.set_fill_color(220, 80, 80)
    pdf.rect(bar_x, bar_y, bar_width, bar_height, "F")

    # Foreground (intact – green)
    intact_width = bar_width * (record.intact_percentage / 100)
    pdf.set_fill_color(50, 180, 80)
    pdf.rect(bar_x, bar_y, intact_width, bar_height, "F")

    # Border
    pdf.set_draw_color(100, 100, 100)
    pdf.rect(bar_x, bar_y, bar_width, bar_height, "D")

    pdf.ln(bar_height + 5)

    # Stats table
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)

    stats = [
        ("Total Images Analyzed", str(record.total_images)),
        ("Intact Count", str(record.intact_count)),
        ("Damaged Count", str(record.damaged_count)),
        ("Average Confidence", f"{record.average_confidence * 100:.1f}%"),
    ]

    for label, value in stats:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, f"{label}:", new_x="END")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # ══════════════════════════════════════════════════════════
    # Section 3: Per-Image Results Table
    # ══════════════════════════════════════════════════════════
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 8, "3. Individual Image Results", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Table header
    col_widths = [10, 60, 35, 35, 40]
    headers = ["#", "Filename", "Classification", "Confidence", "Processing Time"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(25, 60, 120)
    pdf.set_text_color(255, 255, 255)

    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=1, fill=True, align="C", new_x="END")
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)

    for idx, result in enumerate(record.image_results, 1):
        # Alternate row colors
        if idx % 2 == 0:
            pdf.set_fill_color(240, 245, 255)
        else:
            pdf.set_fill_color(255, 255, 255)

        # Check if we need a new page
        if pdf.get_y() > 260:
            pdf.add_page()
            # Reprint header
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(25, 60, 120)
            pdf.set_text_color(255, 255, 255)
            for w, h in zip(col_widths, headers):
                pdf.cell(w, 8, h, border=1, fill=True, align="C", new_x="END")
            pdf.ln()
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)

        # Classification color
        classification_display = result.classification.upper()

        pdf.cell(col_widths[0], 7, str(idx), border=1, fill=True, align="C", new_x="END")

        # Truncate filename if too long
        display_name = result.original_filename
        if len(display_name) > 28:
            display_name = display_name[:25] + "..."
        pdf.cell(col_widths[1], 7, display_name, border=1, fill=True, new_x="END")

        # Color-code classification
        if result.classification == "intact":
            pdf.set_text_color(34, 139, 34)
        else:
            pdf.set_text_color(200, 50, 50)
        pdf.cell(col_widths[2], 7, classification_display, border=1, fill=True, align="C", new_x="END")
        pdf.set_text_color(0, 0, 0)

        pdf.cell(col_widths[3], 7, f"{result.confidence * 100:.1f}%", border=1, fill=True, align="C", new_x="END")
        pdf.cell(col_widths[4], 7, f"{result.processing_time_ms:.1f} ms", border=1, fill=True, align="C", new_x="END")
        pdf.ln()

    pdf.ln(5)

    # ══════════════════════════════════════════════════════════
    # Section 4: Notes
    # ══════════════════════════════════════════════════════════
    if record.notes:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(0, 8, "4. Notes", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 6, record.notes)
        pdf.ln(5)

    # ══════════════════════════════════════════════════════════
    # Section 5: Disclaimer
    # ══════════════════════════════════════════════════════════
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 5, (
        "Disclaimer: This report was generated by an AI-based analysis system. "
        "Results are intended to assist clinical decision-making and should not be "
        "used as the sole basis for diagnosis. Always consult a qualified specialist "
        "for final assessment."
    ))

    # ── Save PDF ─────────────────────────────────────────────
    report_filename = f"report_{record.session_id}_{uuid.uuid4().hex[:6]}.pdf"
    report_path = os.path.join(settings.REPORTS_DIR, report_filename)
    pdf.output(report_path)

    print(f"📄  PDF report generated: {report_path}")
    return report_path
