from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.vessel import Vessel
from app.schemas.vessel import VesselCreate, VesselResponse
import traceback

router = APIRouter()

# 1. GET ALL VESSELS
@router.get("/", response_model=List[VesselResponse])
async def read_vessels(db: AsyncSession = Depends(get_db)):
    try:
        # We need to map DB 'imo' to Pydantic 'imo_number' for the response
        result = await db.execute(select(Vessel))
        vessels = result.scalars().all()
        
        # Manual mapping ensures response matches Pydantic Schema
        response_data = []
        for v in vessels:
            response_data.append({
                "imo_number": v.imo, # <--- MAP DB 'imo' TO API 'imo_number'
                "name": v.name,
                "vessel_type": v.vessel_type,
                "flag": v.flag, # Ensure your Model has this column or remove it
                "is_active": v.is_active
            })
        return response_data
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 2. CREATE VESSEL
@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
async def create_vessel(
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check if exists (Using v.imo)
        result = await db.execute(select(Vessel).where(Vessel.imo == vessel_in.imo_number))
        if result.scalars().first():
            raise HTTPException(
                status_code=400, 
                detail=f"Vessel with IMO {vessel_in.imo_number} already exists."
            )

        new_vessel = Vessel(
            imo=vessel_in.imo_number, # <--- CRITICAL FIX: DB column is 'imo'
            name=vessel_in.name,
            vessel_type=vessel_in.vessel_type,
            # flag=vessel_in.flag # Uncomment if you added 'flag' to models/vessel.py
        )

        db.add(new_vessel)
        await db.commit()
        await db.refresh(new_vessel)
        
        # Return mapped object
        return {
            "imo_number": new_vessel.imo,
            "name": new_vessel.name,
            "vessel_type": new_vessel.vessel_type,
            "is_active": new_vessel.is_active
        }
        
    except Exception as e:
        print(f"❌ Error creating vessel: {e}")
        raise HTTPException(status_code=500, detail=str(e))