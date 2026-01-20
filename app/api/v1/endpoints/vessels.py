from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.vessel import Vessel
from app.schemas.vessel import VesselCreate, VesselResponse
import traceback
from app.schemas.defect import VesselUserResponse

router = APIRouter()

# 1. GET ALL VESSELS
@router.get("/", response_model=List[VesselResponse])
async def read_vessels(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Vessel))
        vessels = result.scalars().all()
        
        # Map DB 'imo' to API 'imo_number'
        response_data = []
        for v in vessels:
            response_data.append({
                "imo_number": v.imo, 
                "name": v.name,
                "vessel_type": v.vessel_type,
                # "code": v.code,     # <--- Ensure this is mapped
                "email": v.email,   # <--- Ensure this is mapped
                "is_active": v.is_active,
                "created_at": v.created_at
            })
        return response_data
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{imo_number}/users", response_model=List[VesselUserResponse])
async def get_users_by_vessel(
    imo_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch all users assigned to a specific vessel IMO"""
    try:
        # Join User -> user_vessel_link -> Vessel
        stmt = select(User).join(User.vessels).where(Vessel.imo == imo_number)
        result = await db.execute(stmt)
        users = result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. CREATE VESSEL
@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
async def create_vessel(
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check duplicate
        result = await db.execute(select(Vessel).where(Vessel.imo == vessel_in.imo_number))
        if result.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail=f"Vessel with IMO {vessel_in.imo_number} already exists."
            )

        new_vessel = Vessel(
            imo=vessel_in.imo_number, 
            name=vessel_in.name,
            vessel_type=vessel_in.vessel_type,
            # CRITICAL: This is where we save the new fields
            # code=vessel_in.code,
            email=vessel_in.email,
            # flag=vessel_in.flag
        )

        db.add(new_vessel)
        await db.commit()
        await db.refresh(new_vessel)
        
        return {
            "imo_number": new_vessel.imo,
            "name": new_vessel.name,
            "vessel_type": new_vessel.vessel_type,
            # "code": new_vessel.code,
            "email": new_vessel.email,
            # "flag": new_vessel.flag,
            "is_active": new_vessel.is_active,
            "created_at": new_vessel.created_at
        }
        
    except Exception as e:
        print(f"❌ Error creating vessel: {e}")
        raise HTTPException(status_code=500, detail=str(e))