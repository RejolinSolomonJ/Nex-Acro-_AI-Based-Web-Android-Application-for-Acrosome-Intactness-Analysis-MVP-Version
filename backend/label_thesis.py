"""
Quick labeling tool for the already-converted thesis images.
Skips conversion (already done), just serves the labeling UI.
Uses: dataset_prep_thesis/ (pre-converted JPGs + existing labels)
"""
import os, sys, json, shutil
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, send_file

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BACKEND_DIR, "dataset_prep_thesis")
DATASET_DIR = os.path.join(BACKEND_DIR, "dataset")
LABELS_FILE = os.path.join(WORK_DIR, "_labels.json")

app = Flask(__name__)

def load_labels():
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_labels(labels):
    with open(LABELS_FILE, "w") as f:
        json.dump(labels, f, indent=2)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acrosome Labeling Tool - Thesis</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0e1a; --card: #1a2035; --border: #1e293b;
            --green: #10b981; --red: #ef4444; --blue: #3b82f6;
            --text: #f1f5f9; --text2: #94a3b8;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }
        body::before {
            content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
            background: radial-gradient(at 20% 50%, rgba(16,185,129,.06) 0%, transparent 60%),
                        radial-gradient(at 80% 20%, rgba(59,130,246,.06) 0%, transparent 60%);
        }
        .c { position:relative; z-index:1; max-width:950px; margin:0 auto; padding:20px; }
        h1 { text-align:center; font-size:1.6rem; font-weight:800; margin-bottom:6px;
             background:linear-gradient(135deg,#10b981,#3b82f6,#8b5cf6);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .sub { text-align:center; color:var(--text2); font-size:.85rem; margin-bottom:18px; }
        .pbar-wrap { background:var(--card); border-radius:12px; padding:14px 18px; margin-bottom:18px; border:1px solid var(--border); }
        .stats { display:flex; gap:20px; justify-content:center; flex-wrap:wrap; margin-bottom:10px; font-size:.82rem; }
        .stats b.g { color:var(--green); } .stats b.r { color:var(--red); } .stats b.b { color:var(--blue); }
        .pbar { height:7px; background:#1e293b; border-radius:4px; overflow:hidden; display:flex; }
        .pbar .fi { background:linear-gradient(90deg,#059669,#10b981); transition:width .3s; }
        .pbar .fd { background:linear-gradient(90deg,#dc2626,#ef4444); transition:width .3s; }
        .icard { background:var(--card); border-radius:16px; border:1px solid var(--border); overflow:hidden; margin-bottom:18px; }
        .ihdr { padding:12px 18px; display:flex; justify-content:space-between; border-bottom:1px solid var(--border); background:rgba(255,255,255,.02); }
        .ihdr .cnt { font-weight:700; color:var(--blue); }
        .ihdr .nm { font-size:.75rem; color:var(--text2); font-family:monospace; }
        .ibox { display:flex; justify-content:center; align-items:center; padding:12px; min-height:380px; background:#0d1117; }
        .ibox img { max-width:100%; max-height:480px; border-radius:6px; object-fit:contain; cursor:zoom-in; transition:transform .3s; }
        .ibox img.z { transform:scale(1.8); cursor:zoom-out; }
        .acts { display:flex; gap:12px; padding:16px; border-top:1px solid var(--border); }
        .btn { flex:1; padding:15px; border:none; border-radius:10px; font-family:'Inter'; font-size:1rem;
               font-weight:700; cursor:pointer; transition:all .2s; text-transform:uppercase; letter-spacing:.5px; }
        .btn:hover { transform:translateY(-2px); }
        .btn:active { transform:scale(.97); }
        .bi { background:linear-gradient(135deg,#059669,#10b981); color:#fff; box-shadow:0 4px 18px rgba(16,185,129,.3); }
        .bd { background:linear-gradient(135deg,#dc2626,#ef4444); color:#fff; box-shadow:0 4px 18px rgba(239,68,68,.3); }
        .bs { flex:.35; background:var(--card); color:var(--text2); border:1px solid var(--border); }
        .nav { display:flex; gap:8px; margin-bottom:16px; }
        .nb { padding:9px 16px; border:1px solid var(--border); background:var(--card); color:var(--text2);
              border-radius:8px; font-family:'Inter'; font-size:.82rem; cursor:pointer; transition:all .2s; }
        .nb:hover { border-color:var(--blue); color:var(--text); }
        .nf { margin-left:auto; background:linear-gradient(135deg,#7c3aed,#8b5cf6); color:#fff; border:none;
              box-shadow:0 4px 18px rgba(139,92,246,.3); }
        .nf:disabled { opacity:.5; cursor:not-allowed; }
        .kb { text-align:center; color:var(--text2); font-size:.75rem; margin-bottom:14px; }
        .kb kbd { background:var(--card); border:1px solid var(--border); border-radius:4px; padding:1px 6px; }
        .done { text-align:center; padding:50px 20px; display:none; }
        .done.active { display:block; }
        .done h2 { font-size:1.8rem; margin-bottom:14px; color:var(--green); }
        .done p { color:var(--text2); margin:6px 0; }
    </style>
</head>
<body>
<div class="c">
    <h1>Acrosome Labeling Tool - Thesis Dataset</h1>
    <p class="sub">Classify each sperm image as <strong>Intact</strong> or <strong>Damaged</strong></p>
    <div class="pbar-wrap">
        <div class="stats">
            <span>Intact: <b class="g" id="ic">0</b></span>
            <span>Damaged: <b class="r" id="dc">0</b></span>
            <span>Remaining: <b id="rc">0</b></span>
            <span>Total: <b class="b" id="tc">0</b></span>
        </div>
        <div class="pbar"><div class="fi" id="ib"></div><div class="fd" id="db"></div></div>
    </div>
    <div class="kb">
        Keyboard: <kbd>&larr;</kbd> Intact &nbsp; <kbd>&rarr;</kbd> Damaged &nbsp; <kbd>S</kbd> Skip &nbsp; <kbd>Z</kbd> Undo &nbsp; <kbd>Space</kbd> Zoom
    </div>
    <div id="lv">
        <div class="icard">
            <div class="ihdr">
                <span class="cnt" id="ctr">1/0</span>
                <span class="nm" id="inm">loading...</span>
            </div>
            <div class="ibox"><img id="cimg" src="" alt="Image" onclick="toggleZoom()"></div>
            <div class="acts">
                <button class="btn bi" onclick="label('intact')" id="bni">Intact</button>
                <button class="btn bs" onclick="skip()">Skip</button>
                <button class="btn bd" onclick="label('damaged')" id="bnd">Damaged</button>
            </div>
        </div>
        <div class="nav">
            <button class="nb" onclick="prev()">Prev</button>
            <button class="nb" onclick="nextUn()">Next Unlabeled</button>
            <button class="nb nf" id="bf" onclick="finish()">Finish & Build Dataset</button>
        </div>
    </div>
    <div class="done" id="ds">
        <h2>Dataset Created!</h2>
        <p id="dsum"></p>
        <p id="dpath" style="margin-top:18px;color:#10b981;font-weight:600"></p>
        <p style="margin-top:10px;color:var(--text2);font-size:.82rem">You can close this page and run training.</p>
    </div>
</div>
<script>
let imgs=[],lbs={},ci=0;
async function init(){const r=await fetch('/api/status');const d=await r.json();imgs=d.images;lbs=d.labels;upd();}
function upd(){
    const ic=Object.values(lbs).filter(l=>l==='intact').length;
    const dc=Object.values(lbs).filter(l=>l==='damaged').length;
    const t=imgs.length, lb=ic+dc;
    document.getElementById('ic').textContent=ic;
    document.getElementById('dc').textContent=dc;
    document.getElementById('rc').textContent=t-lb;
    document.getElementById('tc').textContent=t;
    document.getElementById('ib').style.width=t>0?(ic/t*100)+'%':'0';
    document.getElementById('db').style.width=t>0?(dc/t*100)+'%':'0';
    if(imgs.length>0){
        const img=imgs[ci];
        document.getElementById('cimg').src='/api/image/'+encodeURIComponent(img);
        document.getElementById('ctr').textContent=(ci+1)+'/'+t;
        document.getElementById('inm').textContent=img;
        const l=lbs[img];
        document.getElementById('bni').style.outline=l==='intact'?'3px solid #34d399':'none';
        document.getElementById('bnd').style.outline=l==='damaged'?'3px solid #f87171':'none';
    }
    document.getElementById('bf').disabled=lb<10;
}
async function label(l){
    const img=imgs[ci]; lbs[img]=l;
    fetch('/api/label',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({image:img,label:l})});
    nextUn();
}
function skip(){if(ci<imgs.length-1){ci++;upd();}}
function prev(){if(ci>0){ci--;upd();}}
function nextUn(){
    for(let i=ci+1;i<imgs.length;i++){if(!lbs[imgs[i]]){ci=i;upd();return;}}
    for(let i=0;i<ci;i++){if(!lbs[imgs[i]]){ci=i;upd();return;}}
    if(ci<imgs.length-1)ci++;
    upd();
}
function toggleZoom(){document.getElementById('cimg').classList.toggle('z');}
async function finish(){
    const lb=Object.keys(lbs).length;
    if(lb<10){alert('Label at least 10 images first.');return;}
    if(!confirm('Build dataset with '+lb+' labeled images?'))return;
    document.getElementById('bf').textContent='Building...';
    document.getElementById('bf').disabled=true;
    const r=await fetch('/api/build_dataset',{method:'POST'});
    const res=await r.json();
    if(res.success){
        document.getElementById('lv').style.display='none';
        document.getElementById('ds').classList.add('active');
        document.getElementById('dsum').textContent=res.intact_count+' intact + '+res.damaged_count+' damaged = '+res.total+' images';
        document.getElementById('dpath').textContent='Saved to: '+res.dataset_path;
    } else { alert('Error: '+res.error); document.getElementById('bf').textContent='Finish & Build Dataset'; document.getElementById('bf').disabled=false; }
}
document.addEventListener('keydown',e=>{
    if(e.target.tagName==='INPUT')return;
    switch(e.key){
        case'ArrowLeft':e.preventDefault();label('intact');break;
        case'ArrowRight':e.preventDefault();label('damaged');break;
        case's':case'S':skip();break;
        case'z':case'Z':prev();break;
        case' ':e.preventDefault();toggleZoom();break;
    }
});
init();
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/api/status")
def api_status():
    images = sorted([f.name for f in Path(WORK_DIR).iterdir()
                     if f.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    labels = load_labels()
    return jsonify({"images": images, "labels": labels})

@app.route("/api/image/<path:filename>")
def api_image(filename):
    filepath = Path(WORK_DIR) / filename
    if filepath.exists():
        return send_file(str(filepath))
    return "Not found", 404

@app.route("/api/label", methods=["POST"])
def api_label():
    data = request.json
    labels = load_labels()
    labels[data["image"]] = data["label"]
    save_labels(labels)
    return jsonify({"ok": True})

@app.route("/api/build_dataset", methods=["POST"])
def api_build_dataset():
    try:
        labels = load_labels()
        intact_dir = Path(DATASET_DIR) / "intact"
        damaged_dir = Path(DATASET_DIR) / "damaged"
        os.makedirs(intact_dir, exist_ok=True)
        os.makedirs(damaged_dir, exist_ok=True)
        ic = dc = 0
        for img, lbl in labels.items():
            src = Path(WORK_DIR) / img
            if not src.exists():
                continue
            if lbl == "intact":
                dst = intact_dir / img
                if not dst.exists():
                    shutil.copy2(src, dst)
                ic += 1
            elif lbl == "damaged":
                dst = damaged_dir / img
                if not dst.exists():
                    shutil.copy2(src, dst)
                dc += 1
        return jsonify({"success": True, "intact_count": ic, "damaged_count": dc,
                        "total": ic + dc, "dataset_path": str(DATASET_DIR)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    labels = load_labels()
    images = sorted([f.name for f in Path(WORK_DIR).iterdir()
                     if f.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    labeled = len(labels)
    remaining = len(images) - labeled
    print("=" * 50)
    print("THESIS DATASET LABELING (NO CONVERSION)")
    print("=" * 50)
    print(f"  Images: {len(images)}  |  Labeled: {labeled}  |  Remaining: {remaining}")
    print(f"  Open: http://localhost:5555")
    print("=" * 50)
    sys.stdout.flush()
    app.run(host="0.0.0.0", port=5555, debug=False)
