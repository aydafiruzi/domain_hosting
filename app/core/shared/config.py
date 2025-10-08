# app/core/shared/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """تنظیمات اصلی برنامه برای PostgreSQL"""
    
    # تنظیمات PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "domain_system")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    
    # DATABASE_URL کامل
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    
    # تنظیمات API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "5000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # تنظیمات Namecheap API
    NAMECHEAP_API_USER: str = os.getenv("NAMECHEAP_API_USER", "")
    NAMECHEAP_API_KEY: str = os.getenv("NAMECHEAP_API_KEY", "")
    NAMECHEAP_SANDBOX: bool = os.getenv("NAMECHEAP_SANDBOX", "True").lower() == "true"
    
    # تنظیمات logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "domain_system.log")
    
    # تنظیمات امنیتی
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# ایجاد instance از تنظیمات
settings = Settings()

def get_settings() -> Settings:
    """دریافت تنظیمات"""
    return settings