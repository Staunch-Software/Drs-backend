from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.defect import Defect
from app.models.user import User
from app.schemas.defect import DefectCreate, DefectResponse
from app.api.deps import get_current_user  # We will create this file next

router = APIRouter()

# GET /api/v1/defects/
@router.get("/", response_model=list[DefectResponse])
async def get_defects(
    vessel_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Defect)

    # 1. IF CREW: Force filter to their own ship
    if current_user.assigned_vessel_imo:
        query = query.where(Defect.vessel_imo == current_user.assigned_vessel_imo)
    
    # 2. IF SHORE: Allow optional filtering
    elif vessel_filter:
        query = query.where(Defect.vessel_imo == vessel_filter)
    
    # 3. Execute
    result = await db.execute(query)
    return result.scalars().all()

# POST /api/v1/defects/
@router.post("/", response_model=DefectResponse)
async def create_defect(
    defect_in: DefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Security check: Shore staff usually don't report technical defects
    if not current_user.assigned_vessel_imo:
        raise HTTPException(status_code=400, detail="Only Vessel Crew can report defects.")

    new_defect = Defect(
        **defect_in.dict(),
        vessel_imo=current_user.assigned_vessel_imo, # Auto-injected from user
        reported_by_id=current_user.id
    )
    
    db.add(new_defect)
    await db.commit()
    await db.refresh(new_defect)
    return new_defect