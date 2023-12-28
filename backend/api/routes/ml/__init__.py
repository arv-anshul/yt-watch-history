from fastapi import APIRouter

from . import ctt

router = APIRouter(prefix="/ml", tags=["ml"])

router.include_router(ctt.router)
