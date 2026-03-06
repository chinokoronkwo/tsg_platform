from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Snob Group Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://snobgroup:snobgroup@db:5432/snobgroup"
    DATABASE_ECHO: bool = False

    # Migration: WordPress MySQL source (for scripts/migrate_data.py)
    SOURCE_MYSQL_URL: str = ""

    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Twilio SMS
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # SendGrid / Resend
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "info@thesnobgroup.com"

    # S3 / Cloudflare R2
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "snobgroup-media"
    S3_PUBLIC_URL: str = ""

    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APPLE_CLIENT_ID: str = ""
    APPLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""

    # Meilisearch
    MEILISEARCH_URL: str = "http://meilisearch:7700"
    MEILISEARCH_MASTER_KEY: str = ""

    # GTM
    GTM_CONTAINER_ID: str = "GTM-WZHPTK8Z"

    # Sentry
    SENTRY_DSN: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
