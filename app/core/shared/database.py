# app/core/shared/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .config import settings

# ایجاد Base برای همه مدل‌ها
Base = declarative_base()

# ایجاد engine ارتباط با PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # بررسی سلامت connection
    pool_recycle=3600,   # بازیابی connection هر 1 ساعت
)

# ایجاد session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """
    dependency برای FastAPI/Flask - ایجاد session برای هر درخواست
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """ایجاد تمام tables در دیتابیس"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """حذف تمام tables (فقط برای تست)"""
    Base.metadata.drop_all(bind=engine)

def test_connection():
    """تست اتصال به دیتابیس"""
    try:
        with engine.connect() as conn:
            print("✅ Connection to PostgreSQL successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False