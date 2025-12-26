"""Rivet API - FastAPI Application.

Run with:
    uvicorn agent_factory.api.main:app --reload --port 8000

Docs at:
    http://localhost:8000/docs
"""
import stripe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from agent_factory.api.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Rivet API...")
    
    # Configure Stripe
    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key
        logger.info("Stripe configured")
    else:
        logger.warning("Stripe secret key not set!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Rivet API...")


# Create FastAPI app
app = FastAPI(
    title="Rivet API",
    description="Voice-First CMMS with AI Schematic Understanding",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rivet.io",
        "https://www.rivet.io",
        "http://localhost:3000",  # Next.js dev
        "http://localhost:5173",  # Vite dev
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from agent_factory.api.routers.stripe import router as stripe_router
from agent_factory.api.routers.users import router as users_router
from agent_factory.api.routers.work_orders import router as work_orders_router

app.include_router(stripe_router, prefix="/api", tags=["Stripe"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(work_orders_router, prefix="/api", tags=["Work Orders"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "rivet-api",
        "stripe_configured": bool(settings.stripe_secret_key),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Rivet API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
