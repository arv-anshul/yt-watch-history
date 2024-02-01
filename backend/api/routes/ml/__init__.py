from fastapi import APIRouter

from . import channel_reco, ctt

router = APIRouter(prefix="/ml", tags=["ml"])

router.include_router(ctt.router)
router.include_router(channel_reco.router)
