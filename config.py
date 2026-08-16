import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-fitness-tracker-production-2026-secure-key-64-bytes-min")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-jwt-fitness-secret-key-production-2026-secure-key-64-bytes-min")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production (HTTPS)
    JWT_COOKIE_CSRF_PROTECT = False  # Keep false for dual API/Web simplicity

    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Detect Vercel serverless environment (AWS Lambda / Vercel only allows write operations in /tmp)
    is_vercel = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    default_sqlite_path = "sqlite:////tmp/fitness.db" if is_vercel else f"sqlite:///{os.path.join(BASE_DIR, 'fitness.db')}"

    # Database configuration
    db_url = os.getenv("DATABASE_URL")
    if not db_url or not db_url.strip():
        db_url = default_sqlite_path
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Anthropic Claude API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Google Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
