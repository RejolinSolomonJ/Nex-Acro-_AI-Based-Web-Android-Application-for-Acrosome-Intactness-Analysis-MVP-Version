"""
Prepare the Thesis 3.2.26 dataset for ML training.

This script:
  1. Converts HEIC images from the thesis dataset to JPG format
  2. Launches a web-based labeling tool for classification (intact/damaged)
  3. After labeling, sorts labeled images into dataset/intact/ and dataset/damaged/

Usage:
  Step 1 - Convert HEIC to JPG:
    python prepare_thesis_dataset.py --convert

  Step 2 - Label images:
    python prepare_thesis_dataset.py --label

  Step 3 - Sort labeled images into dataset:
    python prepare_thesis_dataset.py --sort

  All steps:
    python prepare_thesis_dataset.py --all
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Configuration ────────────────────────────────────────────────
THESIS_DIR = r"C:\Users\Rejolin Solomon J\Downloads\Thesis 3.2.26"
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERTED_DIR = os.path.join(BACKEND_DIR, "dataset_prep_thesis")
LABELS_FILE = os.path.join(CONVERTED_DIR, "_labels.json")
DATASET_DIR = os.path.join(BACKEND_DIR, "dataset")


def convert_heic_to_jpg():
    """Convert all HEIC files from the thesis dataset to JPG."""
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        print("[ERROR] pillow-heif is not installed. Installing now...")
        os.system(f"{sys.executable} -m pip install pillow-heif")
        from pillow_heif import register_heif_opener
        register_heif_opener()

    from PIL import Image

    os.makedirs(CONVERTED_DIR, exist_ok=True)

    heic_files = sorted(Path(THESIS_DIR).glob("*.heic")) + sorted(Path(THESIS_DIR).glob("*.HEIC"))
    total = len(heic_files)

    if total == 0:
        print("[WARN] No HEIC files found in the thesis directory.")
        return

    print(f"\n{'='*60}")
    print(f"HEIC -> JPG CONVERSION")
    print(f"{'='*60}")
    print(f"  Source     : {THESIS_DIR}")
    print(f"  Output     : {CONVERTED_DIR}")
    print(f"  Files found: {total}")
    print(f"{'='*60}\n")

    converted = 0
    skipped = 0
    errors = 0

    for i, heic_path in enumerate(heic_files, 1):
        jpg_name = heic_path.stem + ".jpg"
        jpg_path = os.path.join(CONVERTED_DIR, jpg_name)

        # Skip if already converted
        if os.path.exists(jpg_path):
            skipped += 1
            print(f"  [{i}/{total}] SKIP  {heic_path.name} (already converted)")
            continue

        try:
            with Image.open(heic_path) as img:
                # Convert to RGB (HEIC might have alpha channel)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(jpg_path, "JPEG", quality=95)
            converted += 1
            print(f"  [{i}/{total}] OK    {heic_path.name} -> {jpg_name}")
        except Exception as e:
            errors += 1
            print(f"  [{i}/{total}] ERROR {heic_path.name}: {e}")

    print(f"\n{'='*60}")
    print(f"  Converted: {converted}")
    print(f"  Skipped  : {skipped}")
    print(f"  Errors   : {errors}")
    print(f"{'='*60}\n")


def run_labeling_tool():
    """Launch a web-based labeling tool for the converted images."""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import urllib.parse
    import threading
    import webbrowser

    if not os.path.exists(CONVERTED_DIR):
        print("[ERROR] Converted images directory not found. Run --convert first.")
        return

    # Load existing labels
    labels = {}
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as f:
            labels = json.load(f)

    # Get all JPG files
    all_images = sorted([
        f for f in os.listdir(CONVERTED_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    unlabeled = [img for img in all_images if img not in labels]
    total = len(all_images)
    labeled_count = len(labels)

    print(f"\n{'='*60}")
    print(f"IMAGE LABELING TOOL")
    print(f"{'='*60}")
    print(f"  Total images  : {total}")
    print(f"  Already labeled: {labeled_count}")
    print(f"  Remaining      : {len(unlabeled)}")
    print(f"{'='*60}")

    if len(unlabeled) == 0:
        print("\n[OK] All images are already labeled!")
        print(f"     Labels saved at: {LABELS_FILE}")

        # Show summary
        intact_count = sum(1 for v in labels.values() if v == "intact")
        damaged_count = sum(1 for v in labels.values() if v == "damaged")
        print(f"     Intact : {intact_count}")
        print(f"     Damaged: {damaged_count}")
        return

    # HTML for the labeling interface
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Acrosome Labeling Tool - Thesis Dataset</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .header {
            width: 100%;
            background: linear-gradient(135deg, #1a1a3e 0%, #2d1b4e 100%);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid #6366f1;
        }
        .header h1 { font-size: 1.5em; color: #a5b4fc; }
        .progress-bar {
            width: 80%;
            max-width: 600px;
            height: 8px;
            background: #1e1e3f;
            border-radius: 4px;
            margin: 15px auto;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #a78bfa);
            border-radius: 4px;
            transition: width 0.3s;
        }
        .stats {
            display: flex;
            gap: 30px;
            justify-content: center;
            margin: 10px 0;
            font-size: 0.9em;
        }
        .stats span { color: #94a3b8; }
        .stats .count { color: #a5b4fc; font-weight: bold; }
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            width: 100%;
            max-width: 900px;
        }
        .image-container {
            width: 100%;
            max-height: 60vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #1a1a2e;
            border-radius: 12px;
            border: 1px solid #2d2d5e;
            overflow: hidden;
            margin: 10px 0;
        }
        .image-container img {
            max-width: 100%;
            max-height: 60vh;
            object-fit: contain;
        }
        .filename {
            color: #94a3b8;
            font-size: 0.85em;
            margin: 5px 0;
        }
        .buttons {
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }
        .btn {
            padding: 16px 48px;
            font-size: 1.2em;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:active { transform: translateY(0); }
        .btn-intact {
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }
        .btn-intact:hover { box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5); }
        .btn-damaged {
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: white;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        }
        .btn-damaged:hover { box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5); }
        .btn-skip {
            background: linear-gradient(135deg, #4b5563, #6b7280);
            color: white;
            padding: 12px 30px;
            font-size: 0.9em;
        }
        .btn-undo {
            background: linear-gradient(135deg, #d97706, #f59e0b);
            color: white;
            padding: 12px 30px;
            font-size: 0.9em;
        }
        .controls-secondary {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .keyboard-hint {
            color: #6b7280;
            font-size: 0.8em;
            margin-top: 15px;
        }
        .keyboard-hint kbd {
            background: #2d2d5e;
            padding: 2px 8px;
            border-radius: 4px;
            margin: 0 2px;
        }
        .done {
            text-align: center;
            padding: 60px;
        }
        .done h2 { color: #10b981; font-size: 2em; margin-bottom: 20px; }
        .done p { color: #94a3b8; font-size: 1.1em; margin: 8px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Acrosome Labeling Tool — Thesis 3.2.26 Dataset</h1>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="stats">
            <span>Progress: <span class="count" id="progressText">0/0</span></span>
            <span>Intact: <span class="count" id="intactCount" style="color:#10b981">0</span></span>
            <span>Damaged: <span class="count" id="damagedCount" style="color:#ef4444">0</span></span>
        </div>
    </div>
    <div class="main" id="mainArea">
        <div class="image-container">
            <img id="currentImage" src="" alt="Loading...">
        </div>
        <div class="filename" id="fileName"></div>
        <div class="buttons">
            <button class="btn btn-intact" onclick="labelImage('intact')">✅ Intact</button>
            <button class="btn btn-damaged" onclick="labelImage('damaged')">❌ Damaged</button>
        </div>
        <div class="controls-secondary">
            <button class="btn btn-undo" onclick="undoLast()">↩ Undo</button>
            <button class="btn btn-skip" onclick="skipImage()">⏭ Skip</button>
        </div>
        <div class="keyboard-hint">
            Keyboard: <kbd>I</kbd> Intact &nbsp; <kbd>D</kbd> Damaged &nbsp; <kbd>S</kbd> Skip &nbsp; <kbd>Z</kbd> Undo
        </div>
    </div>

    <script>
        const IMAGES = __IMAGES_JSON__;
        const labels = __LABELS_JSON__;
        let currentIndex = 0;
        let history = [];
        let intactCount = Object.values(labels).filter(v => v === 'intact').length;
        let damagedCount = Object.values(labels).filter(v => v === 'damaged').length;

        function updateUI() {
            const totalLabeled = Object.keys(labels).length;
            const total = IMAGES.length + totalLabeled;
            document.getElementById('progressFill').style.width = 
                ((totalLabeled / total) * 100) + '%';
            document.getElementById('progressText').textContent = 
                totalLabeled + '/' + total;
            document.getElementById('intactCount').textContent = intactCount;
            document.getElementById('damagedCount').textContent = damagedCount;

            if (currentIndex >= IMAGES.length) {
                document.getElementById('mainArea').innerHTML = `
                    <div class="done">
                        <h2>🎉 All Done!</h2>
                        <p>All ${total} images have been labeled.</p>
                        <p>Intact: ${intactCount} | Damaged: ${damagedCount}</p>
                        <p style="margin-top: 30px; color: #6366f1;">
                            You can close this window now.<br>
                            Run <code>python prepare_thesis_dataset.py --sort</code> to add them to the dataset.
                        </p>
                    </div>`;
                return;
            }

            const img = IMAGES[currentIndex];
            document.getElementById('currentImage').src = '/image/' + encodeURIComponent(img);
            document.getElementById('fileName').textContent = 
                `${img}  (${currentIndex + 1} of ${IMAGES.length} remaining)`;
        }

        function labelImage(label) {
            if (currentIndex >= IMAGES.length) return;
            const img = IMAGES[currentIndex];
            labels[img] = label;
            history.push({ image: img, label: label });
            
            if (label === 'intact') intactCount++;
            else damagedCount++;

            // Save to server
            fetch('/save_label', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: img, label: label })
            });

            currentIndex++;
            updateUI();
        }

        function skipImage() {
            if (currentIndex >= IMAGES.length) return;
            IMAGES.push(IMAGES[currentIndex]);
            currentIndex++;
            updateUI();
        }

        function undoLast() {
            if (history.length === 0) return;
            const last = history.pop();
            delete labels[last.image];
            
            if (last.label === 'intact') intactCount--;
            else damagedCount--;

            // Remove from server
            fetch('/save_label', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: last.image, label: null })
            });

            // Put image back at current position
            currentIndex--;
            IMAGES[currentIndex] = last.image;
            updateUI();
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'i' || e.key === 'I') labelImage('intact');
            else if (e.key === 'd' || e.key === 'D') labelImage('damaged');
            else if (e.key === 's' || e.key === 'S') skipImage();
            else if (e.key === 'z' || e.key === 'Z') undoLast();
        });

        updateUI();
    </script>
</body>
</html>"""

    # Inject data into HTML
    html_content = html_content.replace(
        "__IMAGES_JSON__", json.dumps(unlabeled)
    ).replace(
        "__LABELS_JSON__", json.dumps(labels)
    )

    class LabelHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html_content.encode())
            elif self.path.startswith("/image/"):
                # Serve image file
                img_name = urllib.parse.unquote(self.path[7:])
                img_path = os.path.join(CONVERTED_DIR, img_name)
                if os.path.exists(img_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.end_headers()
                    with open(img_path, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404)
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == "/save_label":
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                img = body["image"]
                label = body["label"]

                if label is None:
                    labels.pop(img, None)
                else:
                    labels[img] = label

                # Save to disk
                with open(LABELS_FILE, "w") as f:
                    json.dump(labels, f, indent=2)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

        def log_message(self, format, *args):
            pass  # Suppress logs

    PORT = 8765
    server = HTTPServer(("0.0.0.0", PORT), LabelHandler)
    print(f"\n  Labeling tool running at: http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop.\n")

    webbrowser.open(f"http://localhost:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Labeling tool stopped.")
        server.server_close()

    # Show final count
    intact_count = sum(1 for v in labels.values() if v == "intact")
    damaged_count = sum(1 for v in labels.values() if v == "damaged")
    print(f"\n  Labels saved: {len(labels)} total")
    print(f"    Intact : {intact_count}")
    print(f"    Damaged: {damaged_count}")


def sort_into_dataset():
    """Sort labeled images into dataset/intact and dataset/damaged folders."""
    if not os.path.exists(LABELS_FILE):
        print("[ERROR] Labels file not found. Run --label first.")
        return

    with open(LABELS_FILE, "r") as f:
        labels = json.load(f)

    if not labels:
        print("[ERROR] No labels found. Run --label first.")
        return

    # Create dataset directories
    intact_dir = os.path.join(DATASET_DIR, "intact")
    damaged_dir = os.path.join(DATASET_DIR, "damaged")
    os.makedirs(intact_dir, exist_ok=True)
    os.makedirs(damaged_dir, exist_ok=True)

    # Count existing images
    existing_intact = len(os.listdir(intact_dir))
    existing_damaged = len(os.listdir(damaged_dir))

    print(f"\n{'='*60}")
    print(f"SORTING IMAGES INTO DATASET")
    print(f"{'='*60}")
    print(f"  Dataset dir  : {DATASET_DIR}")
    print(f"  Existing     : {existing_intact} intact, {existing_damaged} damaged")
    print(f"  New labels   : {len(labels)}")
    print(f"{'='*60}\n")

    copied = 0
    skipped = 0
    errors = 0

    for img_name, label in sorted(labels.items()):
        src = os.path.join(CONVERTED_DIR, img_name)
        if label == "intact":
            dst = os.path.join(intact_dir, img_name)
        elif label == "damaged":
            dst = os.path.join(damaged_dir, img_name)
        else:
            continue

        if not os.path.exists(src):
            print(f"  [MISS]  {img_name} — source not found")
            errors += 1
            continue

        if os.path.exists(dst):
            skipped += 1
            continue

        shutil.copy2(src, dst)
        copied += 1
        print(f"  [COPY]  {img_name} → {label}/")

    # Final count
    final_intact = len(os.listdir(intact_dir))
    final_damaged = len(os.listdir(damaged_dir))

    print(f"\n{'='*60}")
    print(f"  Copied : {copied}")
    print(f"  Skipped: {skipped} (already exist)")
    print(f"  Errors : {errors}")
    print(f"{'='*60}")
    print(f"\n  DATASET TOTALS:")
    print(f"    Intact  : {final_intact}")
    print(f"    Damaged : {final_damaged}")
    print(f"    TOTAL   : {final_intact + final_damaged}")
    print(f"{'='*60}\n")


def show_status():
    """Show current status of the dataset preparation."""
    print(f"\n{'='*60}")
    print(f"DATASET PREPARATION STATUS")
    print(f"{'='*60}")

    # Thesis source
    heic_count = len(list(Path(THESIS_DIR).glob("*.heic"))) + len(list(Path(THESIS_DIR).glob("*.HEIC")))
    print(f"\n  [SRC] Thesis source: {THESIS_DIR}")
    print(f"     HEIC images: {heic_count}")

    # Converted images
    if os.path.exists(CONVERTED_DIR):
        jpg_count = len([f for f in os.listdir(CONVERTED_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        print(f"\n  [CVT] Converted dir: {CONVERTED_DIR}")
        print(f"     JPG images: {jpg_count}")
    else:
        print(f"\n  [CVT] Converted dir: NOT YET CREATED")

    # Labels
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as f:
            labels = json.load(f)
        intact = sum(1 for v in labels.values() if v == "intact")
        damaged = sum(1 for v in labels.values() if v == "damaged")
        print(f"\n  [LBL] Labels file: {LABELS_FILE}")
        print(f"     Total labeled: {len(labels)}")
        print(f"     Intact: {intact}, Damaged: {damaged}")
    else:
        print(f"\n  [LBL] Labels: NOT YET CREATED")

    # Dataset
    intact_dir = os.path.join(DATASET_DIR, "intact")
    damaged_dir = os.path.join(DATASET_DIR, "damaged")
    intact_count = len(os.listdir(intact_dir)) if os.path.exists(intact_dir) else 0
    damaged_count = len(os.listdir(damaged_dir)) if os.path.exists(damaged_dir) else 0
    print(f"\n  [DST] Dataset: {DATASET_DIR}")
    print(f"     Intact : {intact_count}")
    print(f"     Damaged: {damaged_count}")
    print(f"     TOTAL  : {intact_count + damaged_count}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Thesis 3.2.26 dataset for ML training")
    parser.add_argument("--convert", action="store_true", help="Convert HEIC images to JPG")
    parser.add_argument("--label", action="store_true", help="Launch labeling web tool")
    parser.add_argument("--sort", action="store_true", help="Sort labeled images into dataset folders")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--all", action="store_true", help="Run convert + label + sort")

    args = parser.parse_args()

    if args.all:
        convert_heic_to_jpg()
        run_labeling_tool()
        sort_into_dataset()
    elif args.convert:
        convert_heic_to_jpg()
    elif args.label:
        run_labeling_tool()
    elif args.sort:
        sort_into_dataset()
    elif args.status:
        show_status()
    else:
        show_status()
        print("Use --convert, --label, --sort, or --all to proceed.")
        print("Use --status to check current state.\n")
