from argon2 import PasswordHasher
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from .redis import redis_rate_limiter, RATE_LIMIT_WINDOW, MAX_ATTEMPTS
import time
import string
from dotenv import load_dotenv
import os

# Password Hasher -----

pwd = PasswordHasher()

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd.verify(hashed_password, plain_password)

# Rate Limiter -----

async def rate_limiter(request: Request):
    client_ip = request.client.host
    path = request.url.path
    now = time.time()
    key = f"rate_limit:{client_ip}:{path}"
    window_start = now - RATE_LIMIT_WINDOW

    try:
        with redis_rate_limiter.pipeline() as pipe:
            # Remove old requests
            pipe.zremrangebyscore(key, 0, window_start)

            # Add current request
            pipe.zadd(key, {str(now): now})

            # Get current window count
            pipe.zcard(key)

            # Delete expired keys
            pipe.expire(key, RATE_LIMIT_WINDOW)

            results = pipe.execute()
            count = results[2]
        
        if count > MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Wait for next 24 hours."
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Try again later."
        )

# OTP Generator -----

def generate_otp(len=6) -> str:
    CHARACTERS = string.digits + string.ascii_lowercase + string.ascii_uppercase

    return "".join(secrets.choice(CHARACTERS) for i in range(len))

# Authorization -----

load_dotenv(dotenv_path=".env")
security = HTTPBasic(
    scheme_name="Admin"
)

def authorize(auth: HTTPBasicCredentials=Depends(security)):
    USERNAME = os.getenv("ADMIN")
    PASSWORD = os.getenv("PASSWORD")
    if not (USERNAME and PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Misconfiguration."
        )

    is_correct_username = secrets.compare_digest(auth.username, USERNAME)
    is_correct_password = secrets.compare_digest(auth.password, PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials.",
            headers={
                "WWW-Authenticate": "Basic"
            },
        )

    return True