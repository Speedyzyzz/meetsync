from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.logging import logger
from backend.app.api.routes import (
    health,
    meetings,
    action_items,
    search,
    exports,
    metrics,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MeetSync platform backend...")
    await init_db()
    logger.info("MeetSync backend startup sequence complete.")
    yield
    logger.info("MeetSync backend shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI-powered meeting intelligence platform converting meetings into structured organizational knowledge.",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(meetings.router, prefix=f"{settings.API_V1_STR}/meetings", tags=["Meetings"])
app.include_router(action_items.router, prefix=f"{settings.API_V1_STR}/action-items", tags=["Action Items"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Search"])
app.include_router(exports.router, prefix=f"{settings.API_V1_STR}/meetings", tags=["Exports"])
app.include_router(metrics.router, prefix=f"{settings.API_V1_STR}/metrics", tags=["Metrics"])

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
    }
