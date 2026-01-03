from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.vessel import Vessel
from app.schemas.vessel import VesselCreate, VesselResponse

router = APIRouter()

@router.post("/", response_model=VesselResponse, status_code=status.HTTP_201_CREATED)
async def create_vessel(
    vessel_in: VesselCreate,
    db: AsyncSession = Depends(get_db)
):
    # 1. Check if Vessel already exists (by IMO)
    result = await db.execute(select(Vessel).where(Vessel.imo_number == vessel_in.imo_number))
    existing_vessel = result.scalars().first()
    
    if existing_vessel:
        raise HTTPException(
            status_code=400, 
            detail=f"Vessel with IMO {vessel_in.imo_number} already exists."
        )

    # 2. Create DB Object
    new_vessel = Vessel(
        imo_number=vessel_in.imo_number,
        name=vessel_in.name,
        vessel_type=vessel_in.vessel_type,
        flag=vessel_in.flag
    )

    db.add(new_vessel)
    await db.commit()
    await db.refresh(new_vessel)
    
    return new_vessel

@router.get("/", response_model=list[VesselResponse])
async def read_vessels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vessel))
    return result.scalars().all()