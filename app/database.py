from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "Server Misconfiguration."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600, #Seconds = 1 hour
    connect_args ={"ssl": {
        "ssl_mode": "VERIFY_IDENTITY",
        "ca": "/etc/ssl/certs/ca-certificates.crt"
    }}
)
SessionMaker = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
base = declarative_base()