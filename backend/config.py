import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gridmind.db")
# Demo/dev fallback so the app boots without a .env (CI + demo mode).
# Always set a real SECRET_KEY in production.
SECRET_KEY = os.getenv("SECRET_KEY") or "gridshield-dev-secret-key-change-in-production"
if os.getenv("SECRET_KEY") is None:
    print("[config] WARNING: SECRET_KEY not set — using insecure dev fallback (demo/CI only).", flush=True)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",") if o.strip()]
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
