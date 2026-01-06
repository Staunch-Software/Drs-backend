# app/api/v1/endpoints/defects.py
from uuid import UUID
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload 

from app.core.database import get_db
from app.models.defect import Defect, Thread, Attachment
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.defect import (
    DefectCreate, 
    DefectResponse, 
    ThreadCreate, 
    ThreadResponse, 
    AttachmentResponse,
    AttachmentBase
)
from app.core.blob_storage import generate_write_sas_url, generate_read_sas_url
from app.api.deps import get_current_user 

# redirect_slashes=False prevents the 307 Redirect that breaks CORS
router = APIRouter(redirect_slashes=False)

# --- GET ALL DEFECTS ---
@router.get("/", response_model=list[DefectResponse])
async def get_defects(
    vessel_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Defect)

    # 1. Logic for Vessel Users (Filter by their assigned ships)
    if current_user.role in [UserRole.CHIEF_ENGINEER, UserRole.MASTER, "VESSEL"]:
        # Extract IMOs from the many-to-many relationship
        # Note: Using .imo to match your PGAdmin screenshot
        user_vessel_imos = [v.imo for v in current_user.vessels]
        
        if user_vessel_imos:
            query = query.where(Defect.vessel_imo.in_(user_vessel_imos))
        else:
            # FALLBACK FOR TESTING: Use the IMO from your screenshot
            query = query.where(Defect.vessel_imo == "9832913")
    
    # 2. Logic for Shore Users
    elif vessel_filter:
        query = query.where(Defect.vessel_imo == vessel_filter)
    
    result = await db.execute(query)
    return result.scalars().all()

# --- SAS GENERATION ---
@router.get("/sas")
async def get_upload_sas(
    blobName: str, 
    current_user: User = Depends(get_current_user)
):
    url = generate_write_sas_url(blobName)
    return {"url": url}

# --- CREATE DEFECT ---
@router.post("/", response_model=DefectResponse)
async def create_defect(
    defect_in: DefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Idempotency Check
    existing = await db.get(Defect, defect_in.id)
    if existing:
        return existing

    # 2. Extract IMO (Fallback to your screenshot IMO for testing)
    user_vessel_imo = current_user.vessels[0].imo if current_user.vessels else "9832913"

    # 3. Map Frontend Schema to SQLAlchemy Model
    new_defect = Defect(
        id=defect_in.id,
        vessel_imo=user_vessel_imo,
        reported_by_id=current_user.id,
        title=defect_in.equipment,           
        equipment_name=defect_in.equipment,  
        description=defect_in.description,
        ships_remarks=defect_in.remarks,     
        priority=defect_in.priority.upper(), # Ensure Uppercase for ENUM
        status=defect_in.status.upper(),     # Ensure Uppercase for ENUM
        responsibility=defect_in.responsibility,
        office_support_required=True if "Yes" in defect_in.officeSupport else False,
        pr_number=defect_in.prNumber,
        pr_status=defect_in.prStatus,
        json_backup_path=defect_in.json_backup_path,
        date_identified=datetime.datetime.strptime(defect_in.date, '%Y-%m-%d') if defect_in.date else None
    )
    
    db.add(new_defect)
    await db.commit()
    await db.refresh(new_defect)
    return new_defect

# --- CREATE THREAD ---
@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    thread_in: ThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Idempotency Check
    existing = await db.get(Thread, thread_in.id)
    if existing:
        # If it exists, load attachments so the response model doesn't crash
        res = await db.execute(select(Thread).where(Thread.id == thread_in.id).options(selectinload(Thread.attachments)))
        return res.scalars().first()

    # 2. Create Thread
    new_thread = Thread(
        id=thread_in.id,
        defect_id=thread_in.defect_id,
        user_id=current_user.id,
        author_role=thread_in.author, 
        body=thread_in.body
    )
    
    db.add(new_thread)
    await db.commit()
    
    # 3. THE CRITICAL FIX: 
    # Do NOT use new_thread.attachments = []. 
    # Use db.refresh to load the relationship asynchronously.
    await db.refresh(new_thread, attribute_names=["attachments"])
    
    return new_thread

# --- CREATE ATTACHMENT ---
@router.post("/attachments", response_model=AttachmentResponse)
async def create_attachment(
    attachment_in: AttachmentBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.get(Attachment, attachment_in.id)
    if existing:
        return existing

    new_attachment = Attachment(
        id=attachment_in.id,
        thread_id=attachment_in.thread_id,
        file_name=attachment_in.file_name,
        file_size=attachment_in.file_size,
        content_type=attachment_in.content_type,
        blob_path=attachment_in.blob_path
    )
    
    db.add(new_attachment)
    await db.commit()
    await db.refresh(new_attachment)
    return new_attachment

# --- GET THREADS (For Shore UI) ---
@router.get("/{defect_id}/threads", response_model=list[ThreadResponse])
async def get_defect_threads(
    defect_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    # Use selectinload to fetch attachments in one go
    query = select(Thread).where(Thread.defect_id == defect_id)\
            .options(selectinload(Thread.attachments))\
            .order_by(Thread.created_at.asc())
    
    result = await db.execute(query)
    threads = result.scalars().all()
    
    # Sign the links so the Shore UI can view them
    for thread in threads:
        for att in thread.attachments:
            att.blob_path = generate_read_sas_url(att.blob_path)
            
    return threads