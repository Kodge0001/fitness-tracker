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

def get_database_uri():
    # Check if running in Vercel / AWS Lambda / Serverless
    is_serverless = (
        os.path.exists("/var/task")
        or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
        or "VERCEL" in os.environ
        or "/var/task" in os.path.abspath(__file__)
    )

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        if db_url.startswith("postgres://"):
            return db_url.replace("postgres://", "postgresql://", 1)
        if "postgresql" in db_url or "postgres" in db_url or "mysql" in db_url:
            return db_url
        if is_serverless and "sqlite" in db_url:
            return "sqlite:////tmp/fitness.db"

    if is_serverless:
        return "sqlite:////tmp/fitness.db"

    base_dir = os.path.abspath(os.path.dirname(__file__))
    return f"sqlite:///{os.path.join(base_dir, 'fitness.db')}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-fitness-tracker-production-2026-secure-key-64-bytes-min")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-jwt-fitness-secret-key-production-2026-secure-key-64-bytes-min")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

    SQLALCHEMY_DATABASE_URI = get_database_uri()
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
    JWT_COOKIE_SECURE = False  # Set to false to support Vercel proxy cookies effortlessly


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
