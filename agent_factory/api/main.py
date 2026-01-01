"""Rivet API - FastAPI Application.

Run with:
    uvicorn agent_factory.api.main:app --reload --port 8000

Docs at:
    http://localhost:8000/docs
"""
import stripe
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from agent_factory.api.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Global MachineStateManager instance (initialized in lifespan)
state_manager: Optional["MachineStateManager"] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global state_manager

    # Startup
    logger.info("Starting Rivet API...")

    # Configure Stripe
    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key
        logger.info("Stripe configured")
    else:
        logger.warning("Stripe secret key not set!")

    # Initialize Factory.io MachineStateManager (optional)
    try:
        from agent_factory.platform.config import load_machine_config
        from agent_factory.platform.state.machine_state_manager import MachineStateManager

        machine_config = load_machine_config()
        state_manager = MachineStateManager(machine_config.machines)
        await state_manager.start()
        logger.info(f"Factory.io polling started ({len(machine_config.machines)} machine(s))")
    except FileNotFoundError:
        logger.info("No machines.yaml found - Factory.io integration disabled")
        state_manager = None
    except Exception as e:
        logger.error(f"Failed to initialize Factory.io integration: {e}", exc_info=True)
        state_manager = None

    yield

    # Shutdown
    logger.info("Shutting down Rivet API...")

    # Stop Factory.io polling
    if state_manager:
        await state_manager.stop()
        logger.info("Factory.io polling stopped")


def get_state_manager() -> "MachineStateManager":
    """
    Dependency for accessing MachineStateManager in routes.

    Raises:
        HTTPException: If Factory.io integration is not available

    Example:
        @app.get("/factory-io/state/{machine_id}")
        async def get_machine_state(
            machine_id: str,
            manager: MachineStateManager = Depends(get_state_manager)
        ):
            state = manager.get_state(machine_id)
            return {"machine_id": machine_id, "state": state}
    """
    if state_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Factory.io integration not available (check logs for configuration)"
        )
    return state_manager


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
from agent_factory.api.routers.manuals import router as manuals_router

app.include_router(stripe_router, prefix="/api", tags=["Stripe"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(work_orders_router, prefix="/api", tags=["Work Orders"])
app.include_router(manuals_router, prefix="/api/manuals", tags=["Manuals"])


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with all dependencies."""
    from agent_factory.rivet_pro.database import RIVETProDatabase
    import time

    start_time = time.time()
    checks = {}

    # Check database connection
    db_healthy = False
    db_provider = None
    db_error = None
    try:
        db = RIVETProDatabase()
        db_provider = db.provider
        db._execute_one("SELECT 1 as test")
        db_healthy = True
        db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_error = str(e)

    checks["database"] = {
        "healthy": db_healthy,
        "provider": db_provider,
        "error": db_error
    }

    # Check Stripe API connectivity
    stripe_healthy = False
    stripe_error = None
    if settings.stripe_secret_key:
        try:
            # Lightweight API call - just retrieve balance (doesn't modify anything)
            balance = stripe.Balance.retrieve()
            stripe_healthy = True
        except stripe.error.StripeError as e:
            logger.error(f"Stripe health check failed: {e}")
            stripe_error = str(e)
    else:
        stripe_error = "Stripe secret key not configured"

    checks["stripe"] = {
        "healthy": stripe_healthy,
        "configured": bool(settings.stripe_secret_key),
        "error": stripe_error
    }

    # Aggregate overall status
    all_healthy = db_healthy and stripe_healthy
    any_degraded = (db_healthy or stripe_healthy) and not all_healthy

    if all_healthy:
        overall_status = "healthy"
    elif any_degraded:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    response_time = time.time() - start_time

    return {
        "status": overall_status,
        "service": "rivet-api",
        "version": "1.0.0",
        "response_time_ms": round(response_time * 1000, 2),
        "checks": checks
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
