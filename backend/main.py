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
from backend.routes import api_router
from backend.websocket import websocket_endpoint
from backend.services.live_poller import poller
from backend.services.batch_processor import batch_processor

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
        print("[GridMind] Gemini API key loaded — AI copilot enabled")
    else:
        print("[GridMind] No Gemini API key — using fallback responses")
    poller_task = asyncio.create_task(poller.start())
    batch_task = asyncio.create_task(batch_processor.start())
    yield
    await poller.stop()
    await batch_processor.stop()
    poller_task.cancel()
    batch_task.cancel()

app = FastAPI(
    title="GridMind AI",
    version="2.0.0",
    description="AI-Powered Renewable Energy Forecasting Platform",
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
    response.headers.setdefault("Server", "GridMind")
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

# The SPA authenticates via Bearer tokens (not cookies), so credentials are not
# required; a wildcard CORS origin is safe here and keeps direct API access
# working from any preview host.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.websocket("/ws/{site_id}")
async def ws_endpoint(websocket: WebSocket, site_id: str, token: str = Query(...)):
    await websocket_endpoint(websocket, token, site_id)

@app.get("/health")
def health():
    return {"status": "ok", "service": "GridMind AI", "version": "2.0.0"}

# Serve frontend static files (production mode) — must be LAST route
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
