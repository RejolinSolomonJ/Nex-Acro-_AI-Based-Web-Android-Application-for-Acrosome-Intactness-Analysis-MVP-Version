"""
PDF Report Generation Service — clean aligned layout.
Uses fpdf2. Page width = 210mm, margins = 15mm each side, usable = 180mm.
"""

import os
import uuid
import tempfile
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw
from fpdf import FPDF

from app.config import settings
from app.models.analysis import AnalysisRecord

# ── Column widths (must sum to 180) ──────────────────────────────────────────
COL = {
    "num":   12,
    "file":  79,
    "class": 45,
    "time":  44,
}
HDRS = ["#", "Filename", "Classification", "Proc. Time"]
ROW_H = 7
HDR_H = 8


class AcrosomeReport(FPDF):
    """Custom FPDF with branded header / footer."""

    def __init__(self, title="Acrosome Intactness Analysis Report"):
        super().__init__()
        self.report_title = title
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Blue bar
        self.set_fill_color(25, 60, 120)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, 4)
        self.cell(180, 10, self.report_title, align="C")
        self.ln(14)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 5,
            "Copyright (c) 2025 Nexacro . All Rights Reserved. | Developed by Lin's Infotech Company Ltd.",
            align="C", new_x="LMARGIN", new_y="NEXT"
        )
        self.cell(
            0, 5,
            f"Page {self.page_no()}/{{nb}}  |  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            align="C",
        )

    def _clean_filename(self, name):
        """Convert name to filesystem-safe string (alphanumeric + underscore)."""
        if not name: return "Unknown"
        import re
        # Replace spaces/special chars with underscore, then strip duplicates
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
        cleaned = cleaned.replace(' ', '_')
        return cleaned if cleaned else "Unknown"

    # ── Helpers ──────────────────────────────────────────────────────────────
    def clean(self, txt):
        if not txt: return ""
        # Helvetica only supports a limited range. Replace non-latin-1 with ?
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    def section_title(self, title: str):
        title = self.clean(title)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(25, 60, 120)
        self.set_fill_color(235, 241, 255)
        self.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv_row(self, label: str, value: str, col_w=60):
        label = self.clean(label)
        value = self.clean(value)
        self.set_font("Helvetica", "B", 10)
        self.cell(col_w, ROW_H, label + ":", new_x="END")
        self.set_font("Helvetica", "", 10)
        self.cell(0, ROW_H, value, new_x="LMARGIN", new_y="NEXT")

    def table_header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(25, 60, 120)
        self.set_text_color(255, 255, 255)
        aligns = ["C", "L", "C", "C"]
        for i, (al, key_hdr) in enumerate(zip(aligns, zip(COL, HDRS))):
            key, hdr = key_hdr
            is_last = (i == len(HDRS) - 1)
            nx = "LMARGIN" if is_last else "RIGHT"
            ny = "NEXT" if is_last else "TOP"
            self.cell(COL[key], HDR_H, hdr, border=1, fill=True, align=al, new_x=nx, new_y=ny)
        self.set_text_color(0, 0, 0)

    def table_row(self, idx: int, result):
        # Overflow page guard
        if self.get_y() > 265:
            self.add_page()
            self.table_header()

        # Set style for the row (Reset colors explicitly)
        self.set_fill_color(255, 255, 255)
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 9)

        # #
        self.cell(COL["num"], ROW_H, str(idx), border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")

        # Filename (truncated)
        name = self.clean(result.original_filename)
        if len(name) > 30:
            name = name[:27] + "..."
        self.cell(COL["file"], ROW_H, name, border=1, fill=True, new_x="RIGHT", new_y="TOP")

        # Classification (coloured)
        cls = result.classification.capitalize()
        if cls.lower() == "intact":
            self.set_text_color(22, 140, 50)
        else:
            self.set_text_color(200, 40, 40)
        self.cell(COL["class"], ROW_H, cls, border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        self.set_text_color(0, 0, 0)

        # Time
        self.cell(COL["time"], ROW_H, f"{result.processing_time_ms:.1f} ms", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")


# ── Main function ─────────────────────────────────────────────────────────────

def generate_analysis_report(
    record: AnalysisRecord,
    title: str = "Acrosome Intactness Analysis Report",
    include_images: bool = False,
    patient_name: Optional[str] = None,
) -> str:
    """
    Generate a cleanly aligned PDF and return the saved file path.
    """
    pdf = AcrosomeReport(title)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Convert to IST (UTC+5:30)
    ist_time = record.created_at.astimezone(ZoneInfo("Asia/Kolkata"))
    
    # ══ Section 1 – Session Information ══════════════════════════════════════
    pdf.section_title("1.  Session Information")
    pdf.kv_row("Patient Name",     record.patient_name or "N/A")
    pdf.kv_row("Session ID",       record.session_id)
    pdf.kv_row("Date & Time IST",  ist_time.strftime("%Y-%m-%d  %I:%M:%S %p"))
    pdf.kv_row("Sample ID",        record.sample_id or "N/A")
    pdf.kv_row("Patient ID",       record.patient_id or "N/A")
    
    # Demographic context
    if record.age: 
        pdf.kv_row("Age", str(record.age), col_w=40)
    if record.education: 
        pdf.kv_row("Education", record.education, col_w=40)
    if record.occupation: 
        pdf.kv_row("Occupation", record.occupation, col_w=40)
    if record.bmi: 
        pdf.kv_row("BMI", f"{record.bmi:.1f}", col_w=40)
    
    # History
    if record.has_medical_history:
        pdf.kv_row("Medical History", record.medical_history_details or "Yes")
    if record.has_surgical_history:
        pdf.kv_row("Surgical History", record.surgical_history_details or "Yes")
    
    # Sexual History
    sexual = []
    if record.sexual_abstinence: sexual.append(f"Abstinence: {record.sexual_abstinence}")
    if record.sexual_lubricants: sexual.append(f"Lubricants: {record.sexual_lubricants}")
    if record.sexual_std_history: sexual.append(f"STD: {record.sexual_std_history}")
    if sexual:
        pdf.kv_row("Sexual History", " | ".join(sexual))

    # Lifestyle
    lifestyle = []
    if record.is_alcoholic: lifestyle.append("Alcoholic")
    if record.is_smoker: lifestyle.append("Smoker")
    if record.is_using_drugs: lifestyle.append("Drug User")
    if record.physical_activity: lifestyle.append("Physically Active")
    
    if lifestyle:
        pdf.kv_row("Lifestyle", ", ".join(lifestyle))
    
    pdf.kv_row("Total Images",     str(record.total_images))
    pdf.kv_row("Processing Time",  f"{record.total_processing_time_ms:.0f} ms")
    pdf.ln(5)

    # ══ Section 2 – Results Summary ══════════════════════════════════════════
    pdf.section_title("2.  Analysis Summary")

    # Big percentage figures
    pdf.set_font("Helvetica", "B", 30)
    pdf.set_text_color(22, 140, 50)
    pdf.cell(90, 16, f"{record.intact_percentage:.1f}%", align="C", new_x="END")
    pdf.set_text_color(200, 40, 40)
    pdf.cell(90, 16, f"{record.damaged_percentage:.1f}%", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(90, 6, "Intact", align="C", new_x="END")
    pdf.cell(90, 6, "Damaged", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Progress bar
    bar_x, bar_y = 15, pdf.get_y()
    bar_w, bar_h = 180, 10
    intact_w = bar_w * (record.intact_percentage / 100)

    pdf.set_fill_color(200, 40, 40)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
    pdf.set_fill_color(22, 140, 50)
    pdf.rect(bar_x, bar_y, intact_w, bar_h, "F")
    pdf.set_draw_color(100, 100, 100)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "D")
    pdf.ln(bar_h + 6)

    # Stats grid (2 columns)
    stats = [
        ("Total Analysed",    str(record.total_images)),
        ("Intact Count",      str(record.intact_count)),
        ("Damaged Count",     str(record.damaged_count)),
        ("Processing Time",   f"{record.total_processing_time_ms:.0f} ms"),
    ]
    for i, (lbl, val) in enumerate(stats):
        if i % 2 == 0:
            pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(45, ROW_H, lbl + ":", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 10)
        if i % 2 == 0:
            pdf.cell(45, ROW_H, val, new_x="RIGHT", new_y="TOP")
        else:
            pdf.cell(0, ROW_H, val, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # Pie Chart Graphic
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        pie_path = tmp.name
    try:
        img = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        intact_angle = int(360 * (record.intact_percentage / 100))
        # Damaged slice
        draw.pieslice([(10, 10), (390, 390)], 0, 360, fill=(200, 40, 40, 255))
        if intact_angle > 0:
            draw.pieslice([(10, 10), (390, 390)], 0, intact_angle, fill=(22, 140, 50, 255))
        img.save(pie_path, "PNG")
        pdf.image(pie_path, x=85, y=pdf.get_y(), w=40)
        pdf.ln(45)
    except Exception as e:
        print(f"Error drawing pie chart: {e}")
    finally:
        if os.path.exists(pie_path):
            os.remove(pie_path)

    # ══ Section 3 – Per-Image Results ════════════════════════════════════════
    pdf.add_page()
    pdf.section_title("3.  Individual Image Results")

    results = record.image_results
    if len(results) == 16:
        # Group into 4 grids of 4
        for grid_idx in range(4):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(180, 8, f"Grid {grid_idx + 1}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.table_header()
            for i in range(4):
                result = results[grid_idx * 4 + i]
                pdf.table_row(i + 1, result)
            pdf.ln(4)
    else:
        # Generic list
        pdf.table_header()
        for idx, result in enumerate(results, 1):
            pdf.table_row(idx, result)
        pdf.ln(6)

    # ══ Section 4 – Notes (if any) ═══════════════════════════════════════════
    if record.notes:
        pdf.section_title("4.  Notes")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, pdf.clean(record.notes))
        pdf.ln(4)

    # ══ Disclaimer ═══════════════════════════════════════════════════════════
    pdf.set_fill_color(250, 250, 240)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 80)
    pdf.multi_cell(
        0, 5,
        "Disclaimer: This report was generated by an AI-based system and is intended to assist "
        "clinical decision-making only. Results should be verified by a qualified medical specialist "
        "before use in diagnosis or treatment.",
        fill=True,
    )

    # ── Save ─────────────────────────────────────────────────────────────────
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    
    # Use patient name if available, otherwise session_id
    id_part = pdf._clean_filename(patient_name) if patient_name else "Report"
    filename = f"NexAcro_Report_{id_part}_{record.session_id}_{uuid.uuid4().hex[:6]}.pdf"
    
    report_path = os.path.join(settings.REPORTS_DIR, filename)
    pdf.output(report_path)
    print(f"[OK] PDF generated: {report_path}")
    return report_path
