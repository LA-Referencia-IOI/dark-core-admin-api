"""
dARK Core Admin API - Main Application Entry Point

FastAPI application with lifespan management, middleware, and routing.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.dependencies import init_orchestrator, shutdown_orchestrator, get_orchestrator
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
    
    # Initialize orchestrator connection to blockchain
    try:
        orchestrator = init_orchestrator()
        logger.info(f"Connected to blockchain at block {orchestrator.get_block_number()}")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down dARK Core Admin API...")
    shutdown_orchestrator()


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
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        try:
            orchestrator = get_orchestrator()
            block = orchestrator.get_block_number()
            admin_balance = orchestrator.get_admin_balance()
            return {
                "status": "healthy",
                "blockchain_connected": True,
                "current_block": block,
                "admin_balance_eth": admin_balance,
            }
        except RuntimeError:
            return {
                "status": "unhealthy",
                "error": "Orchestrator not initialized"
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
