"""
Acrosome Intactness Analysis – FastAPI Application

Main entry point assembling all routes, middleware, and lifecycle events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import connect_to_database, close_database_connection
from app.routes import auth, analysis, analytics, reports


# ── Application Lifecycle ────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    # Startup
    print("🚀  Starting Acrosome Intactness Analysis API...")
    await connect_to_database()
    yield
    # Shutdown
    await close_database_connection()
    print("👋  Server shut down.")


# ── Create Application ───────────────────────────────────────
app = FastAPI(
    title="Acrosome Intactness Analysis API",
    description=(
        "🔬 AI-powered API for analyzing microscopic sperm images to detect "
        "acrosome intactness using CNN-based classification.\n\n"
        "**Features:**\n"
        "- Upload multiple microscope images for batch analysis\n"
        "- CNN-based classification (Intact / Damaged)\n"
        "- Percentage-based reporting\n"
        "- PDF report generation\n"
        "- Analytics dashboard data\n"
        "- JWT authentication\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ──────────────────────────────────────────
# Allow frontend apps (web + Android WebView) to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # React dev server
        "http://localhost:5173",       # Vite dev server
        "http://localhost:8080",       # Android emulator
        "http://10.0.2.2:8000",       # Android emulator → host
        "*",                           # Allow all for MVP (tighten in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount Static Files ───────────────────────────────────────
# Serve uploaded images (for preview in admin panel)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")


# ── Include Routers ──────────────────────────────────────────
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(analytics.router)
app.include_router(reports.router)


# ── Health Check ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """API root – health check."""
    return {
        "service": "Acrosome Intactness Analysis API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    from app.ml.predict import get_model_info
    return {
        "status": "healthy",
        "database": "connected",
        "model": get_model_info(),
    }
