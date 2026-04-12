import redis
from redis.asyncio import from_url
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")
REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL")
REDIS_RATE_LIMITER_URL = os.getenv("REDIS_RATE_LIMITER_URL")
REDIS_OTP_STORAGE_URL = os.getenv("REDIS_OTP_STORAGE_URL")
if not (REDIS_CACHE_URL and REDIS_RATE_LIMITER_URL and REDIS_OTP_STORAGE_URL):
    raise ValueError(
        "Server Misconfiguration."
    )

# Redis Cache -----

redis_cache = redis.from_url(
    REDIS_CACHE_URL,
    decode_responses=True
)

CACHE_TTL = 86400 #Seconds = 24 hours

# Redis Rate Limiter -----

redis_rate_limiter = redis.from_url(
    REDIS_RATE_LIMITER_URL,
    decode_responses=True
)

RATE_LIMIT_WINDOW = 86400 #Seconds = 24 hours
MAX_ATTEMPTS = 3

# Redis OTP Storage -----

redis_otp_storage = from_url(
    REDIS_OTP_STORAGE_URL,
    decode_responses=True
)

OTP_TTL = 600 #Seconds = 10 minutes