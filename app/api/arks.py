"""
Global ARKs endpoints for Admin.

Provides operations for getting global statistics and history of ARKs.
"""

import logging
import time
from threading import Lock
from typing import Callable

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

# Scanning ARKCreated logs is expensive on a busy chain, and these values only
# need to be roughly fresh for dashboard widgets. Serve them from a short-lived
# process-local cache so bursts of dashboard loads cost one RPC scan, not many.
_CACHE_TTL_SECONDS = 30.0
_cache: dict[str, tuple[float, object]] = {}
_cache_lock = Lock()


def _cached(key: str, producer: Callable[[], object]) -> object:
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit is not None and now - hit[0] < _CACHE_TTL_SECONDS:
            return hit[1]
    value = producer()
    with _cache_lock:
        _cache[key] = (time.monotonic(), value)
    return value


@router.get(
    "/count",
    response_model=ArkCountResponse,
    summary="Get total ARK count",
    description="Get the total number of ARKs registered on the blockchain.",
)
def get_ark_count(
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> ArkCountResponse:
    """Get total number of ARKs."""
    logger.info("Getting total ARK count")

    count = _cached("count", corelib_client.get_ark_count)
    return ArkCountResponse(count=count)


@router.get(
    "/recent",
    response_model=RecentArksResponse,
    summary="Get recent ARKs",
    description="Get the most recent ARKs registered on the blockchain, including their metadata CIDs.",
)
def get_recent_arks(
    limit: int = Query(10, ge=1, le=100, description="Number of recent ARKs to retrieve"),
    cert_info: dict = Depends(require_mtls),
    corelib_client: DARKCoreClient = Depends(get_corelib_client),
) -> RecentArksResponse:
    """Get the most recent ARKs."""
    logger.info(f"Getting last {limit} recent ARKs")

    recent = _cached(
        f"recent:{limit}",
        lambda: corelib_client.get_recent_arks(limit=limit),
    )

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
