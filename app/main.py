"""
dARK Core Admin API - Main Application Entry Point

FastAPI application with lifespan management, middleware, and routing.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.dependencies import (
    get_corelib_client,
    init_corelib_client,
    shutdown_corelib_client,
)
from app.api.router import api_router
from app.exceptions.handlers import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Initializes resources on startup and cleans up on shutdown.
    """
    # Startup
    logger.info("Starting dARK Core Admin API...")
    settings = get_settings()
    
    # Validate mTLS config if enabled
    if settings.mtls_enabled:
        settings.validate_mtls_config()
        logger.info("mTLS is enabled")
    else:
        logger.warning("mTLS is disabled - for development only!")
    
    # Initialize blockchain client
    try:
        corelib_client = init_corelib_client()
        logger.info(f"Connected to blockchain at block {corelib_client.get_block_number()}")
    except Exception as e:
        logger.error(f"Failed to initialize dark-core-lib client: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down dARK Core Admin API...")
    shutdown_corelib_client()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()
    
    app = FastAPI(
        title="dARK Core Admin API",
        description=(
            "REST API service for dARK Authority management. "
            "Provides administrative operations for the Admin Node."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware (configurable for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Cheap process liveness check; does not call RPC or storage."""
        return {"status": "alive"}

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        try:
            corelib_client = get_corelib_client()
            block = corelib_client.get_block_number()
            admin_balance = corelib_client.get_admin_balance()
            return {
                "status": "healthy",
                "blockchain_connected": True,
                "current_block": block,
                "admin_balance_eth": admin_balance,
            }
        except RuntimeError:
            return {
                "status": "unhealthy",
                "error": "dark-core-lib client not initialized"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return app


# Create app instance
app = create_app()


def run_server():
    """Run the server (used by CLI)."""
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.admin_api_host,
        port=settings.admin_api_port,
        reload=False,
    )
