import os
import time as _time
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import init_db

# Load .env file
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Load Gemini API key
    from backend.gemini_copilot import _has_api_key
    if _has_api_key():
        print("[Bottleneck] Gemini API key loaded — AI copilot enabled")
    else:
        print("[Bottleneck] No Gemini API key — using deterministic fallback advisor")
    yield

app = FastAPI(
    title="Bottleneck AI",
    version="3.0.0",
    description="Power Outage Prediction & Grid Equipment Failure Advisor",
    lifespan=lifespan,
)

# Security headers: opaque, CSP-safe baseline for the SPA
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    response.headers.setdefault("Server", "Bottleneck")
    return response

# Request ID + latency tracing for observability
@app.middleware("http")
async def request_tracing(request: Request, call_next):
    request_id = request.headers.get("x-request-id", f"req_{int(_time.time()*1000)}")
    start = _time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((_time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bottleneck routes (and /api/gs backward compatible alias)
from backend.bottleneck.routes import router as bottleneck_router, gs_alias_router
app.include_router(bottleneck_router)
app.include_router(gs_alias_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Bottleneck AI", "version": "3.0.0"}

# Serve frontend static files (production mode) — must be LAST route
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

