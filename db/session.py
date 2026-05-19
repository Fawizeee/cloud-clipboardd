from sqlalchemy import create_engine
from db.models.base import Base  # single shared Base for all models
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv
load_dotenv()
# from app.core.config import settings
#get database api from .env file
#get db url from env
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
# Create database engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    # Connection health checks 
    pool_pre_ping= True,
    echo=False,
    
    # Connection pool optimization
    # Optimized for remote databases (Supabase cloud)
    poolclass=QueuePool,
    pool_size=10,              # Reduced for remote DB (maintains fewer idle connections)
    max_overflow=20,           # Allow 20 extra under load (total 30)
    pool_timeout=10,           # Reduced timeout (fail faster if pool exhausted)
    pool_recycle=1800,         # Recycle connections every 30 minutes (more frequent for remote)
    # Connection arguments for psycopg2 (PostgreSQL driver)
    connect_args={
        "connect_timeout": 5,  # Connection timeout in seconds
        "options": "-c tcp_keepalives_idle=30 -c tcp_keepalives_interval=10 -c tcp_keepalives_count=5"
    },
    
    # Query optimization
    execution_options={
        "compiled_cache_size": 500  # Cache 500 compiled queries
    }
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is imported from db.models.base (single source of truth)


# Dependency: yields a DB session per request, then closes it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

