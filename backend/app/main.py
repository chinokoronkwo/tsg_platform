from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .core.config import get_settings
from .core.exceptions import register_exception_handlers
from .middleware.security_headers import SecurityHeadersMiddleware
from .middleware.request_validation import RequestValidationMiddleware
from .middleware.rate_limit import RateLimitExceeded, rate_limit_exception_handler
from .api.v1 import router as api_v1_router

settings = get_settings()

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        environment="production" if not settings.DEBUG else "development",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

app.include_router(api_v1_router, prefix="/api/v1")

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
