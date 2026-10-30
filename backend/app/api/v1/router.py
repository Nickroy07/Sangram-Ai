"""Aggregated API Router for Sangram AI Backend.

Combines all domain routers under their respective prefixes and tags.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.battles import router as battles_router
from app.api.v1.billing import router as billing_router
from app.api.v1.models import router as models_router
from app.api.v1.saved import router as saved_router
from app.api.v1.shares import router as shares_router
from app.api.v1.support import router as support_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter()

# Register domain routers under the /api prefix
api_v1_router.include_router(battles_router)
api_v1_router.include_router(shares_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(saved_router)
api_v1_router.include_router(billing_router)
api_v1_router.include_router(support_router)
