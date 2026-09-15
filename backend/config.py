import os
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gridmind.db")

# Determine run environment.  Anything other than explicit "development" or
# "test" is treated as production-like and REQUIRES a real SECRET_KEY.
_ENV = os.getenv("APP_ENV", "production").lower()
_IS_DEV_OR_TEST = _ENV in ("development", "test")

_SECRET_KEY_ENV = os.getenv("SECRET_KEY")

if _SECRET_KEY_ENV:
    SECRET_KEY = _SECRET_KEY_ENV
elif _IS_DEV_OR_TEST:
    # Safe only in local dev / CI — never reaches production because APP_ENV
    # would need to be explicitly set to "development" or "test".
    SECRET_KEY = "gridshield-dev-secret-key-not-for-production"
    print(
        "[config] WARNING: SECRET_KEY not set — using insecure dev fallback. "
        "Set APP_ENV=production and a real SECRET_KEY before deploying.",
        flush=True,
    )
else:
    # Production with no secret = hard fail rather than silent insecure fallback.
    print(
        "[config] FATAL: SECRET_KEY environment variable is required in production. "
        "Set a strong random value and restart.",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(1)

# Algorithm is pinned server-side; the env var is only for
# legitimate operational overrides (e.g. RS256 with key rotation).
# Reject obviously wrong values to prevent algorithm-confusion attacks.
_ALLOWED_ALGORITHMS = {"HS256", "HS384", "HS512"}
_ALGORITHM_ENV = os.getenv("ALGORITHM", "HS256").upper()
if _ALGORITHM_ENV not in _ALLOWED_ALGORITHMS:
    print(
        f"[config] FATAL: Unsupported JWT ALGORITHM '{_ALGORITHM_ENV}'. "
        f"Allowed: {_ALLOWED_ALGORITHMS}",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(1)
ALGORITHM = _ALGORITHM_ENV

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",") if o.strip()]
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
# Stricter limit applied to authentication endpoints only
AUTH_RATE_LIMIT_PER_MINUTE = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10"))
