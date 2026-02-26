# 🔬 Acrosome Intactness Analysis – Backend & ML

AI-powered backend for analyzing microscopic sperm images to detect acrosome intactness using CNN-based classification.

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py             # Settings (from .env)
│   ├── database.py           # MongoDB async connection
│   ├── models/
│   │   ├── user.py           # User document model
│   │   ├── analysis.py       # Analysis record model
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── routes/
│   │   ├── auth.py           # Register, Login, Profile
│   │   ├── analysis.py       # Upload & Analyze images
│   │   ├── analytics.py      # Dashboard statistics
│   │   └── reports.py        # PDF report generation
│   ├── services/
│   │   ├── ai_service.py     # Analysis orchestration pipeline
│   │   └── pdf_service.py    # PDF report generation
│   ├── ml/
│   │   ├── model.py          # CNN architectures (MobileNetV2 + Custom)
│   │   ├── preprocessing.py  # Image preprocessing pipeline
│   │   ├── predict.py        # Inference service (single + batch)
│   │   └── train.py          # Model training pipeline
│   └── utils/
│       └── security.py       # JWT, password hashing, auth deps
├── run.py                    # Start server
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── .gitignore
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your MongoDB URL and secret key
```

### 3. Run the Server

```bash
python run.py
```

Server starts at **http://localhost:8000**
- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login (returns JWT) |
| GET | `/api/auth/me` | Get current user profile |

### Analysis (Core)
| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | **`/api/analysis/analyze`** | **Upload images → AI analysis → intact %** |
| GET | `/api/analysis/result/{id}` | Get results by analysis ID |
| GET | `/api/analysis/session/{session_id}` | Get results by session |
| GET | `/api/analysis/list` | List all analyses (paginated) |
| DELETE | `/api/analysis/{id}` | Delete an analysis |
| GET | `/api/analysis/model-info` | ML model status |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/summary` | Summary stats for dashboard |
| GET | `/api/analytics/detailed?days=30` | Daily breakdown |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reports/generate` | Generate PDF report |
| GET | `/api/reports/download/{filename}` | Download PDF |

## 🔬 Core Analysis Flow

```
Upload Images → Validate → Preprocess (CLAHE + Denoise + Resize)
      → CNN Batch Prediction → Compute Intact %
      → Save to MongoDB → Return Results
```

### Example: Analyze Images

```bash
curl -X POST http://localhost:8000/api/analysis/analyze \
  -F "files=@sperm_image_1.jpg" \
  -F "files=@sperm_image_2.jpg" \
  -F "files=@sperm_image_3.jpg" \
  -F "sample_id=SAMPLE_001" \
  -F "patient_id=PAT_123"
```

### Response:
```json
{
  "id": "65a1b2c3d4e5f6...",
  "session_id": "sess_abc123def456",
  "total_images": 3,
  "intact_count": 2,
  "damaged_count": 1,
  "intact_percentage": 66.67,
  "damaged_percentage": 33.33,
  "average_confidence": 0.89,
  "image_results": [
    {
      "filename": "sess_abc123_1a2b3c4d.jpg",
      "original_filename": "sperm_image_1.jpg",
      "classification": "intact",
      "confidence": 0.92,
      "processing_time_ms": 45.2
    },
    ...
  ],
  "total_processing_time_ms": 152.8
}
```

## 🧠 ML Model

### Architecture Options

1. **MobileNetV2 (Recommended)** – Transfer learning, 3.4M params, mobile-ready
2. **Custom CNN** – 4-block architecture for training from scratch

### Training

```bash
# Prepare dataset:
#   dataset/
#   ├── intact/    (images of intact acrosomes)
#   └── damaged/   (images of damaged acrosomes)

python -m app.ml.train --data_dir ./dataset --model_type mobilenet --epochs 50
```

### Mock Mode

If no trained model file exists, the API automatically uses **mock predictions** for development and testing. Once you train a model, place it at `ml_models/acrosome_cnn_model.h5` and restart.

## 🔧 Tech Stack

- **Framework:** FastAPI (async, auto-docs)
- **ML:** TensorFlow / Keras (MobileNetV2 CNN)
- **Database:** MongoDB (Motor + Beanie ODM)
- **Auth:** JWT (python-jose) + bcrypt
- **PDF:** fpdf2
- **Image Processing:** OpenCV + Pillow
