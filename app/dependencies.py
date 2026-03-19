"""
Dependency injection for FastAPI.

Provides singleton instances of the dark-core-lib client.
"""

import logging
from typing import Optional

from dark_core_lib import DARKCoreClient, CoreConfig
from dark_core_lib.exceptions import ConfigurationError

from app.config import get_settings

logger = logging.getLogger(__name__)

# Singleton dark-core-lib client instance
_corelib_client: Optional[DARKCoreClient] = None


def get_corelib_client() -> DARKCoreClient:
    """
    Get the DARKCoreClient singleton instance.

    Returns:
        DARKCoreClient instance

    Raises:
        RuntimeError: If client not initialized
    """
    global _corelib_client
    if _corelib_client is None:
        raise RuntimeError(
            "dark-core-lib client not initialized. "
            "Call init_corelib_client() during application startup."
        )
    return _corelib_client


def init_corelib_client() -> DARKCoreClient:
    """
    Initialize the DARKCoreClient singleton.

    Called during application lifespan startup.

    Returns:
        Initialized DARKCoreClient

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _corelib_client

    settings = get_settings()
    settings.validate_blockchain_config()

    logger.info("Initializing DARKCoreClient...")

    config = CoreConfig(
        rpc_url=settings.dark_rpc_url,
        chain_id=settings.dark_chain_id,
        authority_contract_address=settings.dark_authority_address,
        dark_contract_address=settings.dark_contract_address,
        admin_private_key=settings.dark_admin_private_key,
        read_only=False,
    )

    _corelib_client = DARKCoreClient(config)
    logger.info("DARKCoreClient initialized successfully")

    return _corelib_client


def shutdown_corelib_client() -> None:
    """Cleanup dark-core-lib client on shutdown."""
    global _corelib_client
    if _corelib_client is not None:
        logger.info("Shutting down DARKCoreClient...")
        _corelib_client = None


# Backward-compatible aliases for local callers still importing old names.
get_orchestrator = get_corelib_client
init_orchestrator = init_corelib_client
shutdown_orchestrator = shutdown_corelib_client
