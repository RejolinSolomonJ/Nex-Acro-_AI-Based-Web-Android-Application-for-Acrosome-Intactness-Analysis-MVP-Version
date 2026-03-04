import os
import sys
import glob
import uuid
from datetime import datetime
from fpdf import FPDF
import argparse
import matplotlib.pyplot as plt

from app.ml.predict import predict_single

class BatchAcrosomeReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(25, 60, 120)
        self.cell(0, 10, "Acrosome Intactness Batch Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(25, 60, 120)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Acrosome AI Analysis System", align="C")

def generate_batch_report(folder_path="test_images", patient_id="Not Provided"):
    print("============================================================")
    print(f"GENERATING BATCH ACROSOME PDF REPORT")
    print(f"Folder: {folder_path} | Patient ID: {patient_id}")
    print("============================================================")

    if not os.path.exists(folder_path):
        print(f"[ERROR] Directory not found: {folder_path}")
        return

    extensions = ('*.jpg', '*.jpeg', '*.png', '*.heic')
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(folder_path, ext)))
        image_paths.extend(glob.glob(os.path.join(folder_path, ext.upper())))
        
    # Deduplicate paths (ignoring case issues on Windows)
    image_paths = list(set([os.path.abspath(p) for p in image_paths]))

    if not image_paths:
        print(f"[WARNING] No images found in {folder_path}.")
        return

    total_images = len(image_paths)
    print(f"Found {total_images} unique images. Analyzing and building PDF...\n")

    results_data = []
    intact_count = 0
    damaged_count = 0

    for idx, img_path in enumerate(image_paths, 1):
        filename = os.path.basename(img_path)
        try:
            with open(img_path, "rb") as f:
                image_bytes = f.read()
            
            result = predict_single(image_bytes)
            classification = result["classification"]
            intact_prob = result["intact_probability"] * 100
            damaged_prob = result["damaged_probability"] * 100

            if classification == "intact":
                intact_count += 1
            else:
                damaged_count += 1
                
            grid_num = ((idx - 1) // 4) + 1
            cell_num = ((idx - 1) % 4) + 1
            
            results_data.append({
                "filename": filename,
                "grid_name": f"Grid {grid_num} - Cell {cell_num}",
                "classification": classification.upper(),
                "intact_prob": intact_prob,
                "damaged_prob": damaged_prob
            })
            print(f"[{idx}/{total_images}] Processed {filename}")
        except Exception as e:
            print(f"[{idx}/{total_images}] ERROR on {filename}: {str(e)}")

    intact_percentage = (intact_count / total_images) * 100 if total_images > 0 else 0

    # ── Create the Pie Chart ──────────────────────────────────────
    session_id = f"batch_{uuid.uuid4().hex[:8]}"
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    chart_path = os.path.join(reports_dir, f"pie_{session_id}.png")
    
    # Generate matplotlib circle bar/pie graph
    plt.figure(figsize=(4, 4))
    if total_images > 0:
        sizes = [intact_count, damaged_count]
        labels = [f'Intact ({intact_count})', f'Damaged ({damaged_count})']
        colors = ['#10b981', '#ef4444']  # Green and Red
        explode = (0.05, 0)
        
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=False, startangle=140, textprops={'fontsize': 10, 'weight': 'bold', 'color': '#111'})
    else:
        plt.pie([1], labels=['No Data'], colors=['#cccccc'])
        
    plt.title('Acrosome Integrity Summary', fontsize=12, pad=10, weight='bold', color='#1e293b')
    plt.tight_layout()
    plt.savefig(chart_path, dpi=150, transparent=True, bbox_inches='tight')
    plt.close()

    # ── Step 2: Build PDF ────────────────────────────────────────
    print("\n[2/2] Generating PDF file...")

    pdf = BatchAcrosomeReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ═══ Section 1: Session Information ═══
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 10, "1. Batch Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_text_color(0, 0, 0)
    info = [
        ("Patient ID", str(patient_id)),
        ("Session ID", session_id),
        ("Date & Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Folder Analyzed", folder_path),
        ("Total Images", str(total_images)),
        ("Overall Intact Rate", f"{intact_percentage:.1f}%")
    ]

    for label, value in info:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(45, 7, f"{label}:", new_x="RIGHT", new_y="TOP")
        
        # Color the percentage
        if label == "Overall Intact Rate":
            pdf.set_font("Helvetica", "B", 12)
            if intact_percentage >= 50:
                pdf.set_text_color(34, 139, 34)
            else:
                pdf.set_text_color(200, 50, 50)
        else:
            pdf.set_font("Helvetica", "", 10)
            
        pdf.cell(0, 7, str(value), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    # Place the generated Pie Chart to the right of the summary
    if os.path.exists(chart_path):
        pdf.image(chart_path, x=115, y=35, w=80)
        
    pdf.set_y(105) # Move below the chart
    pdf.ln(5)

    # ═══ Section 2: Detailed Results Table ═══
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(25, 60, 120)
    pdf.cell(0, 10, "2. Individual Image Results", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Improved Alignment: Table Header
    col_widths = [45, 45, 50, 50]
    total_table_width = sum(col_widths)
    # Center the table on an A4 page (width 210, margins 10 left & right -> usable 190. Offset = (190 - 190)/2 = 0)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(25, 60, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_widths[0], 8, "Grid No.", border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
    pdf.cell(col_widths[1], 8, "Classification", border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
    pdf.cell(col_widths[2], 8, "Intact %", border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
    pdf.cell(col_widths[3], 8, "Damaged %", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)

    # Table Rows
    for i, res in enumerate(results_data):
        if i % 2 == 0:
            pdf.set_fill_color(240, 245, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(col_widths[0], 6, res['grid_name'], border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        
        pdf.set_font("Helvetica", "B", 9)
        if res['classification'] == "INTACT":
            pdf.set_text_color(34, 139, 34)
        else:
            pdf.set_text_color(200, 50, 50)
            
        pdf.cell(col_widths[1], 6, res['classification'], border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(34, 139, 34)
        pdf.cell(col_widths[2], 6, f"{res['intact_prob']:.1f}%", border=1, fill=True, align="C", new_x="RIGHT", new_y="TOP")
        
        pdf.set_text_color(200, 50, 50)
        pdf.cell(col_widths[3], 6, f"{res['damaged_prob']:.1f}%", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # ═══ Disclaimer ═══
    # If near the bottom, add a new page (roughly Y > 250)
    if pdf.get_y() > 250:
        pdf.add_page()
        
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 4, (
        "DISCLAIMER: This report was generated by an AI-based analysis system using a "
        "Convolutional Neural Network (ResNet50). Results are intended to assist clinical "
        "decision-making and should NOT be used as the sole basis for diagnosis or treatment. "
        "Always consult a qualified reproductive specialist for final assessment."
    ))

    # ── Save PDF ──────────────────────────────────────────────────
    patient_clean = "".join(c for c in patient_id if c.isalnum() or c in ('-', '_')).strip()
    if not patient_clean: patient_clean = "Unknown"
    
    report_name = f"Batch_Report_{patient_clean}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    report_path = os.path.join(reports_dir, report_name)
    pdf.output(report_path)

    # Cleanup temp pie chart
    if os.path.exists(chart_path):
        os.remove(chart_path)

    print(f"\n[OK] Batch Report successfully saved to:\n  -> {report_path}")
    print(f"Open this PDF to view the summary!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate batch report with Patient ID")
    parser.add_argument("--folder", type=str, default="test_images", help="Folder containing images")
    parser.add_argument("--patient_id", type=str, default="Not Provided", help="Patient ID to include in the report")
    args = parser.parse_args()
    
    generate_batch_report(folder_path=args.folder, patient_id=args.patient_id)
