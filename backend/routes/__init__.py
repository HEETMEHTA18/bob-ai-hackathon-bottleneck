from fastapi import APIRouter
from backend.routes.auth import router as auth_router
from backend.routes.sites import router as sites_router
from backend.routes.forecast import router as forecast_router
from backend.routes.data import router as data_router
from backend.routes.insights import router as insights_router
from backend.routes.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(sites_router)
api_router.include_router(forecast_router)
api_router.include_router(data_router)
api_router.include_router(insights_router)
api_router.include_router(chat_router)
