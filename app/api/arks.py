"""
Global ARKs endpoints for Admin.

Provides operations for getting global statistics and history of ARKs.
"""

import logging

from fastapi import APIRouter, Depends, Query

from dark_core_lib import DARKCoreClient

from app.dependencies import get_corelib_client
from app.middleware.auth import require_mtls
from app.models.responses import (
    ArkCountResponse,
    RecentArksResponse,
    RecentArkItem
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/count",
    response_model=ArkCountResponse,
    summary="Get total ARK count",
    description="Get the total number of ARKs registered on the blockchain.",
)
async def get_ark_count(
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> ArkCountResponse:
    """Get total number of ARKs."""
    logger.info("Getting total ARK count")
    
    count = corelib_client.get_ark_count()
    return ArkCountResponse(count=count)


@router.get(
    "/recent",
    response_model=RecentArksResponse,
    summary="Get recent ARKs",
    description="Get the most recent ARKs registered on the blockchain, including their metadata CIDs.",
)
async def get_recent_arks(
    limit: int = Query(10, ge=1, le=100, description="Number of recent ARKs to retrieve"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> RecentArksResponse:
    """Get the most recent ARKs."""
    logger.info(f"Getting last {limit} recent ARKs")
    
    recent = corelib_client.get_recent_arks(limit=limit)
    
    # Map raw dictionary results to Pydantic models
    items = []
    for r in recent:
        items.append(
            RecentArkItem(
                pid=r["pid"],
                naan=r["naan"],
                name=r["name"],
                owner=r["owner"],
                url=r["url"],
                cid=r["cid"]
            )
        )
        
    return RecentArksResponse(limit=limit, arks=items)
