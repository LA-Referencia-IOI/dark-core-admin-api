"""
API Router aggregation.

Combines all endpoint routers into a single router.
"""

from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.arks import router as arks_router

api_router = APIRouter()

# Admin endpoints
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin"],
)

# ARKs endpoints
api_router.include_router(
    arks_router,
    prefix="/arks",
    tags=["ARKs"],
)
