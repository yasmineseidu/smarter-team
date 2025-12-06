"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan handler."""
    setup_logging()
    yield


app = FastAPI(
    title="Smarter Team API",
    description="Multi-Agent AI Agency Automation",
    version="0.1.0",
    lifespan=lifespan,
)

setup_cors(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Smarter Team API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Import and include routers
# from src.api.routes import leads, agents, webhooks
# app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
