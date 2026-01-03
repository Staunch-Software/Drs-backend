from fastapi import APIRouter
from app.api.v1.endpoints import auth, defects, vessels # <--- Import vessels

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/login", tags=["auth"])
api_router.include_router(defects.router, prefix="/defects", tags=["defects"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"]) # <--- Add this