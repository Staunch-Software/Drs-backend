from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/access-token")
async def login_access_token(form_data: LoginRequest):
    # SIMULATED DB CHECK (Replace with real DB logic later)
    if form_data.username == "chief" and form_data.password == "12345":
        return {
            "access_token": "fake-jwt-token-vessel", 
            "token_type": "bearer",
            "role": "VESSEL",
            "name": "Chief Engineer"
        }
    
    if form_data.username == "manager" and form_data.password == "12345":
        return {
            "access_token": "fake-jwt-token-shore", 
            "token_type": "bearer",
            "role": "SHORE",
            "name": "Fleet Manager"
        }
        
    raise HTTPException(status_code=400, detail="Incorrect email or password")