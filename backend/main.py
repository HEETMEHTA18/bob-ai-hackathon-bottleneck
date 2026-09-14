import os
import time as _time
import asyncio
from pathlib import Path
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.database import init_db
from backend.routes import api_router
from backend.websocket import websocket_endpoint
from backend.services.live_poller import poller
from backend.services.batch_processor import batch_processor
from backend.config import CORS_ORIGINS, RATE_LIMIT_PER_MINUTE

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

    # Seed demo user if not exists
    from backend.auth import get_password_hash
    from backend.database import get_db
    from sqlalchemy import select
    from backend.models_db import User
    async for db in get_db():
        result = await db.execute(select(User).where(User.email == "demo@gridshield.ai"))
        if not result.scalar_one_or_none():
            import uuid
            demo_user = User(
                id=str(uuid.uuid4()),
                email="demo@gridshield.ai",
                hashed_password=get_password_hash("demo1234"),
                full_name="Demo User",
                role="viewer",
                is_active=True,
            )
            db.add(demo_user)
            await db.commit()
            print("[GridShield] Demo user seeded")
        break

    # Load Gemini API key
    from backend.gemini_copilot import _has_api_key
    if _has_api_key():
        print("[GridShield] Gemini API key loaded — AI copilot enabled")
    else:
        print("[GridShield] No Gemini API key — using deterministic fallback advisor")
    poller_task = asyncio.create_task(poller.start())
    batch_task = asyncio.create_task(batch_processor.start())
    yield
    await poller.stop()
    await batch_processor.stop()
    poller_task.cancel()
    batch_task.cancel()

app = FastAPI(
    title="GridShield AI",
    version="3.0.0",
    description="Power Outage Prediction & Grid Equipment Failure Advisor",
    lifespan=lifespan,
)

# Security headers: CSP-safe baseline for the SPA
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:8000 http://localhost:5173; "
        "frame-ancestors 'none'"
    )
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers.setdefault("Server", "GridShield")
    return response

# Rate limiting: simple in-memory token bucket per IP
_rate_buckets: dict[str, list[float]] = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = _time.time()
    window = 60.0

    # Clean old entries
    _rate_buckets[client_ip] = [t for t in _rate_buckets[client_ip] if now - t < window]

    if len(_rate_buckets[client_ip]) >= RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": str(int(window - (now - _rate_buckets[client_ip][0])))},
        )

    _rate_buckets[client_ip].append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_PER_MINUTE - len(_rate_buckets[client_ip])))
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

# CORS — whitelist specific origins from env
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router)

# GridShield routes (new domain — coexists with Gridkavach routes)
from backend.gridshield.routes import router as gridshield_router
app.include_router(gridshield_router)

@app.websocket("/ws/{site_id}")
async def ws_endpoint(websocket: WebSocket, site_id: str, token: str = Query(...)):
    await websocket_endpoint(websocket, token, site_id)

@app.get("/health")
def health():
    return {"status": "ok", "service": "GridShield AI", "version": "3.0.0"}

# Serve frontend static files (production mode) — must be LAST route
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("ws/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="WebSocket endpoint — use ws:// protocol")
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
