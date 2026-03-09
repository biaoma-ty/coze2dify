from fastapi import APIRouter

from .endpoints import conversion, coze_source, devmode, platform, sync, validation

api_router = APIRouter()
api_router.include_router(coze_source.router, prefix="/coze", tags=["coze"])
api_router.include_router(conversion.router, prefix="/convert", tags=["conversion"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(validation.router, prefix="/validate", tags=["validation"])
api_router.include_router(platform.router, prefix="/platform", tags=["platform"])
api_router.include_router(devmode.router, prefix="/devmode", tags=["devmode"])
