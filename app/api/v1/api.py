from fastapi import APIRouter
from app.api.v1.endpoints import auth, defects, vessels, users # <--- 1. Import users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/login", tags=["auth"])
api_router.include_router(defects.router, prefix="/defects", tags=["defects"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])
api_router.include_router(users.router, prefix="/users", tags=["users"]) # <--- 2. Add this line