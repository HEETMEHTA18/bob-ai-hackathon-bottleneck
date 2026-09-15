import uuid
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

# ALGORITHM is already validated in config.py (only HMAC variants allowed).
# Pin it here so decode() never accepts attacker-supplied algorithms.
_DECODE_ALGORITHMS = [ALGORITHM]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> tuple[str, str]:
    """Returns (encoded_token, jti).  Caller must persist jti for revocation."""
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": jti,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM), jti


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT.  Returns payload or None on any error."""
    try:
        # algorithms= is a list; never accept 'none' or unexpected algorithms.
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=_DECODE_ALGORITHMS,
            options={"verify_exp": True},
        )
        return payload
    except JWTError:
        return None
