"""
API Router aggregation.

Combines all endpoint routers into a single router.
"""

from fastapi import APIRouter

from app.api.admin import router as admin_router

api_router = APIRouter()

# Admin endpoints
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin"],
)
