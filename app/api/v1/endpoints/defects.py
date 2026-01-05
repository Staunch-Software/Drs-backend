from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.defect import Defect, Thread, Attachment
from app.models.user import User
from app.schemas.defect import (
    DefectCreate, 
    DefectResponse, 
    ThreadCreate, 
    ThreadResponse, 
    AttachmentResponse,
    AttachmentBase
)
from app.core.blob_storage import generate_write_sas_url
from app.api.deps import get_current_user 
import datetime
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from app.core.config import settings

router = APIRouter()

# GET /api/v1/defects/
@router.get("/", response_model=list[DefectResponse])
async def get_defects(
    vessel_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Defect)
    if current_user.assigned_vessel_imo:
        query = query.where(Defect.vessel_imo == current_user.assigned_vessel_imo)
    elif vessel_filter:
        query = query.where(Defect.vessel_imo == vessel_filter)
    
    result = await db.execute(query)
    return result.scalars().all()

# SAS Generation Endpoint (Module 3)
@router.get("/sas")
async def get_upload_sas(
    blobName: str,
    current_user: User = Depends(get_current_user)
):
    # Use your reference-based logic to generate the signed URL
    url = generate_write_sas_url(blobName)
    return {"url": url}

# POST /api/v1/defects/ (Idempotent & Mapped)
@router.post("/", response_model=DefectResponse)
async def create_defect(
    defect_in: DefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Security check
    if not current_user.assigned_vessel_imo:
        raise HTTPException(status_code=400, detail="Only Vessel Crew can report defects.")

    # 2. Idempotency Check (Prevents duplicates if UI retries)
    existing = await db.get(Defect, defect_in.id)
    if existing:
        return existing

    # 3. Map Frontend Schema to SQLAlchemy Model
    new_defect = Defect(
        id=defect_in.id,
        vessel_imo=current_user.assigned_vessel_imo,
        reported_by_id=current_user.id,
        
        # Mapping to your existing columns
        title=defect_in.equipment,           
        equipment_name=defect_in.equipment,  
        description=defect_in.description,
        ships_remarks=defect_in.remarks,     
        
        priority=defect_in.priority,
        status=defect_in.status,
        responsibility=defect_in.responsibility,
        
        # Map 'Yes/No' string to Boolean for your existing column
        office_support_required=True if "Yes" in defect_in.officeSupport else False,
        
        pr_number=defect_in.prNumber,
        pr_status=defect_in.prStatus,
        json_backup_path=defect_in.json_backup_path,
        
        # Convert string date to python datetime
        date_identified=datetime.datetime.strptime(defect_in.date, '%Y-%m-%d') if defect_in.date else None
    )
    
    db.add(new_defect)
    await db.commit()
    await db.refresh(new_defect)
    return new_defect

@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    thread_in: ThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Idempotency Check
    existing = await db.get(Thread, thread_in.id)
    if existing:
        return existing

    # 2. Create Thread
    new_thread = Thread(
        id=thread_in.id,
        defect_id=thread_in.defect_id,
        author=thread_in.author,
        body=thread_in.body
    )
    
    db.add(new_thread)
    await db.commit()
    await db.refresh(new_thread)
    return new_thread

# POST /api/v1/defects/attachments
@router.post("/attachments", response_model=AttachmentResponse)
async def create_attachment(
    attachment_in: AttachmentBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Idempotency Check
    existing = await db.get(Attachment, attachment_in.id)
    if existing:
        return existing

    # 2. Create Attachment Metadata
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

# GET /api/v1/defects/{id}/threads (For Shore UI to see conversation)
@router.get("/{defect_id}/threads", response_model=list[ThreadResponse])
async def get_defect_threads(defect_id: UUID, db: AsyncSession = Depends(get_db)):
    query = select(Thread).where(Thread.defect_id == defect_id).order_by(Thread.created_at.asc())
    result = await db.execute(query)
    threads = result.scalars().all()
    
    # 🔥 Add this to make the Shore UI work immediately
    from app.core.blob_storage import generate_read_sas_url
    for thread in threads:
        for att in thread.attachments:
            # Convert clean path to a temporary secure link
            att.blob_path = generate_read_sas_url(att.blob_path)
            
    return threads