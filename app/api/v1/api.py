from fastapi import APIRouter
from app.api.v1.endpoints import auth, defects, vessels, users 

api_router = APIRouter()

# Register the Login Route
api_router.include_router(auth.router, prefix="/login", tags=["auth"])

# Register other routes
api_router.include_router(defects.router, prefix="/defects", tags=["defects"])
api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])
api_router.include_router(users.router, prefix="/users", tags=["users"])