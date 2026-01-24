import uuid
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload 
import logging

from app.core.database import get_db
from app.models.defect import Defect, Thread, Attachment, PrEntry
from app.models.user import User
from app.models.enums import UserRole, DefectStatus, DefectPriority, DefectSource
from app.models.vessel import Vessel
from app.schemas.defect import (
    DefectCreate, DefectUpdate, DefectResponse, 
    ThreadCreate, ThreadResponse, AttachmentResponse, AttachmentBase,
    DefectCloseRequest, VesselUserResponse,
    PrEntryCreate, PrEntryResponse
)
from app.core.blob_storage import generate_write_sas_url, generate_read_sas_url
from app.api.deps import get_current_user 
from app.services.email_service import send_defect_email 
from app.services.notification_service import notify_vessel_users, create_task_for_mentions

logger = logging.getLogger(__name__)
router = APIRouter(redirect_slashes=False)

def prepare_email_data(defect: Defect):
    """Safely converts defect object to dictionary for email template"""
    priority_str = defect.priority.value if hasattr(defect.priority, "value") else str(defect.priority)
    status_str = defect.status.value if hasattr(defect.status, "value") else str(defect.status)
    defect_source_str = defect.defect_source.value if hasattr(defect.defect_source, "value") else str(defect.defect_source)
    
    return {
        "vessel_imo": defect.vessel_imo,
        "title": defect.title,
        "equipment_name": defect.equipment_name,
        "priority": priority_str,
        "status": status_str,
        "defect_source": defect_source_str,
        "description": defect.description
    }

# --- GET ALL DEFECTS ---
@router.get("/", response_model=list[DefectResponse])
async def get_defects(
    vessel_imo: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Defect).options(
        selectinload(Defect.vessel),
        selectinload(Defect.pr_entries)
    )

    query = query.where(Defect.is_deleted == False)

    if current_user.role == UserRole.VESSEL:
        user_vessel_imos = [v.imo for v in current_user.vessels]
        if not user_vessel_imos:
            return []
        query = query.where(Defect.vessel_imo.in_(user_vessel_imos))
    elif vessel_imo:
        query = query.where(Defect.vessel_imo == vessel_imo)

    result = await db.execute(query)
    defects = result.scalars().all()
    
    for defect in defects:
        defect.vessel_name = defect.vessel.name if defect.vessel else None
    
    return defects

# --- SAS GENERATION ---
@router.get("/sas")
async def get_upload_sas(blobName: str, current_user: User = Depends(get_current_user)):
    """Generate upload SAS URL for blob storage"""
    try:
        logger.info(f"📝 Generating upload SAS for: {blobName}")
        url = generate_write_sas_url(blobName)
        logger.info(f"✅ Upload SAS generated successfully")
        return {"url": url}
    except Exception as e:
        logger.error(f"❌ Error generating upload SAS: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

# --- CREATE DEFECT ---
@router.post("/", response_model=DefectResponse)
async def create_defect(
    defect_in: DefectCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new defect with comprehensive error handling"""
    try:
        logger.info(f"📝 Creating defect: {defect_in.id}")
        logger.info(f"   Vessel IMO: {defect_in.vessel_imo}")
        logger.info(f"   Equipment: {defect_in.equipment}")
        logger.info(f"   Defect Source: {defect_in.defect_source}")
        
        # Check if defect already exists
        existing = await db.get(Defect, defect_in.id)
        if existing:
            logger.info(f"⚠️ Defect {defect_in.id} already exists, returning existing")
            await db.refresh(existing, attribute_names=["pr_entries"])
            return existing

        # Validate vessel authorization
        if current_user.role == UserRole.VESSEL:
            authorized_imos = [v.imo for v in current_user.vessels]
            if defect_in.vessel_imo not in authorized_imos:
                logger.error(f"❌ User {current_user.id} not authorized for vessel {defect_in.vessel_imo}")
                raise HTTPException(status_code=403, detail="Not authorized for this vessel")

        # Parse priority with fallback
        try:
            priority_enum = DefectPriority(defect_in.priority.upper())
            logger.info(f"   Priority: {priority_enum}")
        except ValueError as e:
            logger.warning(f"⚠️ Invalid priority '{defect_in.priority}', using NORMAL. Error: {e}")
            priority_enum = DefectPriority.NORMAL

        # Parse status with fallback
        try:
            status_enum = DefectStatus(defect_in.status.upper())
            logger.info(f"   Status: {status_enum}")
        except ValueError as e:
            logger.warning(f"⚠️ Invalid status '{defect_in.status}', using OPEN. Error: {e}")
            status_enum = DefectStatus.OPEN

        # ✅ Parse Defect Source with fallback
        try:
            defect_source_enum = DefectSource(defect_in.defect_source)
            logger.info(f"   Defect Source: {defect_source_enum}")
        except ValueError as e:
            logger.warning(f"⚠️ Invalid defect source '{defect_in.defect_source}', using INTERNAL_AUDIT. Error: {e}")
            defect_source_enum = DefectSource.INTERNAL_AUDIT

        # Parse dates with comprehensive error handling
        date_id = None
        if defect_in.date:
            try:
                date_id = datetime.strptime(defect_in.date, '%Y-%m-%d')
                logger.info(f"   Date Identified: {date_id}")
            except ValueError as e:
                logger.error(f"❌ Invalid date format '{defect_in.date}': {e}")
                try:
                    # Try ISO format as fallback
                    date_id = datetime.fromisoformat(defect_in.date.replace('Z', '+00:00'))
                except Exception as e2:
                    logger.error(f"❌ Failed to parse date with fallback: {e2}")
                    date_id = datetime.now()  # Use current date as last resort

        target_date = None
        if defect_in.target_close_date:
            try:
                target_date = datetime.strptime(defect_in.target_close_date, '%Y-%m-%d')
                logger.info(f"   Target Close Date: {target_date}")
            except ValueError as e:
                logger.error(f"❌ Invalid target date format '{defect_in.target_close_date}': {e}")
                try:
                    target_date = datetime.fromisoformat(defect_in.target_close_date.replace('Z', '+00:00'))
                except Exception:
                    target_date = None

        # ✅ Create defect with all fields
        new_defect = Defect(
            id=defect_in.id,
            vessel_imo=defect_in.vessel_imo,
            reported_by_id=current_user.id,  # ✅ CRITICAL: Use authenticated user
            title=defect_in.equipment,           
            equipment_name=defect_in.equipment,  
            description=defect_in.description,
            defect_source=defect_source_enum,  # ✅ NEW FIELD
            priority=priority_enum,  
            status=status_enum,
            responsibility=defect_in.responsibility,
            json_backup_path=defect_in.json_backup_path,
            date_identified=date_id,
            target_close_date=target_date
        )
        
        logger.info("💾 Adding defect to database...")
        db.add(new_defect)
        
        logger.info("💾 Committing transaction...")
        await db.commit()
        
        logger.info("🔄 Refreshing defect with relationships...")
        await db.refresh(new_defect, attribute_names=["pr_entries", "vessel"])

        logger.info("✅ Defect created successfully")

        # Get vessel name for notifications
        vessel = await db.get(Vessel, new_defect.vessel_imo)
        vessel_name = vessel.name if vessel else new_defect.vessel_imo

        # Send notifications
        logger.info("📢 Sending notifications to vessel users...")
        await notify_vessel_users(
            db=db,
            vessel_imo=new_defect.vessel_imo,
            vessel_name=vessel_name,
            title="New Defect Reported",
            message=f"{current_user.full_name} reported: {new_defect.title}",
            exclude_user_id=current_user.id,
            defect_id=str(new_defect.id)
        )
        await db.commit()

        # Send email notification
        logger.info("📧 Scheduling email notification...")
        email_data = prepare_email_data(new_defect)
        background_tasks.add_task(send_defect_email, email_data, "CREATED")
        
        logger.info(f"🎉 Defect {new_defect.id} creation complete")
        return new_defect

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR creating defect: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create defect: {str(e)}"
        )

# ✅ NEW: CREATE PR ENTRY
@router.post("/pr-entries", response_model=PrEntryResponse)
async def create_pr_entry(
    pr_in: PrEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new PR entry for a defect"""
    try:
        logger.info(f"📝 Creating PR entry for defect {pr_in.defect_id}: {pr_in.pr_number}")
        
        defect = await db.get(Defect, pr_in.defect_id)
        if not defect:
            logger.error(f"❌ Defect {pr_in.defect_id} not found")
            raise HTTPException(status_code=404, detail="Defect not found")
        
        new_pr = PrEntry(
            id=uuid.uuid4(),
            defect_id=pr_in.defect_id,
            pr_number=pr_in.pr_number,
            pr_description=pr_in.pr_description,
            created_by_id=current_user.id
        )
        
        db.add(new_pr)
        await db.commit()
        await db.refresh(new_pr)
        
        logger.info(f"✅ PR entry created: {new_pr.id}")
        return new_pr
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating PR entry: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ✅ NEW: GET PR ENTRIES FOR DEFECT
@router.get("/{defect_id}/pr-entries", response_model=list[PrEntryResponse])
async def get_pr_entries(
    defect_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all PR entries for a defect"""
    try:
        query = select(PrEntry).where(PrEntry.defect_id == defect_id).order_by(PrEntry.created_at.asc())
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"❌ Error fetching PR entries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ✅ NEW: DELETE PR ENTRY
@router.delete("/pr-entries/{pr_id}")
async def delete_pr_entry(
    pr_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a PR entry"""
    try:
        pr_entry = await db.get(PrEntry, pr_id)
        if not pr_entry:
            raise HTTPException(status_code=404, detail="PR entry not found")
        
        await db.delete(pr_entry)
        await db.commit()
        
        logger.info(f"🗑️ PR entry {pr_id} deleted")
        return {"message": "PR entry deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting PR entry: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- CREATE THREAD ---
@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    thread_in: ThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new thread/comment"""
    try:
        existing = await db.get(Thread, thread_in.id)
        if existing:
            res = await db.execute(select(Thread).where(Thread.id == thread_in.id).options(selectinload(Thread.attachments)))
            return res.scalars().first()

        new_thread = Thread(
            id=thread_in.id,
            defect_id=thread_in.defect_id,
            user_id=current_user.id,
            author_role=thread_in.author, 
            body=thread_in.body,
            tagged_user_ids=thread_in.tagged_user_ids
        )
        
        db.add(new_thread)
        
        if thread_in.tagged_user_ids:
            defect = await db.get(Defect, thread_in.defect_id)
            await create_task_for_mentions(
                db=db,
                defect_id=thread_in.defect_id,
                defect_title=defect.title if defect else "Defect",
                creator_id=current_user.id,
                tagged_user_ids=thread_in.tagged_user_ids
            )
        await db.commit()
        await db.refresh(new_thread, attribute_names=["attachments"])
        return new_thread
        
    except Exception as e:
        logger.error(f"❌ Error creating thread: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- CREATE ATTACHMENT (with file size validation) ---
@router.post("/attachments", response_model=AttachmentResponse)
async def create_attachment(
    attachment_in: AttachmentBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create attachment metadata with file size validation"""
    try:
        existing = await db.get(Attachment, attachment_in.id)
        if existing: 
            logger.info(f"⚠️ Attachment {attachment_in.id} already exists")
            return existing

        # ✅ File size validation (1MB limit)
        MAX_FILE_SIZE = 1024 * 1024  # 1MB in bytes
        if attachment_in.file_size and attachment_in.file_size > MAX_FILE_SIZE:
            logger.error(f"❌ File size exceeds limit: {attachment_in.file_size} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File '{attachment_in.file_name}' exceeds 1MB limit ({attachment_in.file_size / 1024 / 1024:.2f}MB)"
            )

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
        
        logger.info(f"✅ Attachment created: {new_attachment.file_name}")
        return new_attachment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating attachment: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- GET THREADS ---
@router.get("/{defect_id}/threads", response_model=list[ThreadResponse])
async def get_defect_threads(defect_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all threads for a defect"""
    try:
        query = select(Thread).where(Thread.defect_id == defect_id)\
                .options(selectinload(Thread.attachments), selectinload(Thread.user))\
                .order_by(Thread.created_at.asc())

        result = await db.execute(query)
        threads = result.scalars().all()

        for thread in threads:
            thread.author_role = thread.user.full_name
                
        return threads
    except Exception as e:
        logger.error(f"❌ Error fetching threads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- GET VESSEL USERS ---
@router.get("/{defect_id}/vessel-users", response_model=list[VesselUserResponse])
async def get_vessel_users_for_defect(defect_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all users assigned to the defect's vessel"""
    try:
        defect = await db.get(Defect, defect_id)
        if not defect: 
            raise HTTPException(status_code=404, detail="Defect not found")
        
        query = select(User).join(User.vessels).where(Vessel.imo == defect.vessel_imo)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return [{"id": str(u.id), "full_name": u.full_name} for u in users]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching vessel users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- UPDATE DEFECT ---
@router.patch("/{defect_id}", response_model=DefectResponse)
async def update_defect(
    defect_id: UUID,
    defect_in: DefectUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing defect"""
    try:
        defect = await db.get(Defect, defect_id)
        if not defect: 
            raise HTTPException(status_code=404, detail="Not found")
        
        old_priority_str = defect.priority.value if hasattr(defect.priority, "value") else str(defect.priority)

        update_data = defect_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "priority":
                try:
                    defect.priority = DefectPriority(value.upper())
                except ValueError:
                    pass
            elif field == "defect_source":  # ✅ NEW
                try:
                    defect.defect_source = DefectSource(value)
                except ValueError:
                    pass
            else:
                setattr(defect, field, value)
                
        await db.commit()
        await db.refresh(defect, attribute_names=["pr_entries"])

        new_priority_str = defect.priority.value if hasattr(defect.priority, "value") else str(defect.priority)
        
        if defect_in.priority and old_priority_str != new_priority_str:
            system_thread = Thread(
                id=uuid.uuid4(),
                defect_id=defect.id,
                user_id=current_user.id,
                author_role="SYSTEM",
                body=f"⚠️ Priority escalated from {old_priority_str} to {new_priority_str} by {current_user.full_name}",
                is_system_message=True
            )
            db.add(system_thread)
            
            vessel = await db.get(Vessel, defect.vessel_imo)
            vessel_name = vessel.name if vessel else defect.vessel_imo
            
            await notify_vessel_users(
                db=db,
                vessel_imo=defect.vessel_imo,
                vessel_name=vessel_name,
                title="Priority Escalated",
                message=f"Priority raised to {new_priority_str} for: {defect.title}",
                exclude_user_id=current_user.id,
                defect_id=str(defect.id)
            )
            await db.commit() 

        email_data = prepare_email_data(defect)
        background_tasks.add_task(send_defect_email, email_data, "UPDATED")

        return defect
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating defect: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- CLOSE DEFECT ---
@router.patch("/{defect_id}/close", response_model=DefectResponse)
async def close_defect(
    defect_id: UUID,
    close_data: DefectCloseRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Close a defect with closure remarks and images"""
    try:
        defect = await db.get(Defect, defect_id)
        if not defect: 
            raise HTTPException(status_code=404, detail="Defect not found")
        
        defect.status = DefectStatus.CLOSED
        defect.closed_at = datetime.now()
        defect.closed_by_id = current_user.id
        defect.closure_remarks = close_data.closure_remarks
        defect.closure_image_before = close_data.closure_image_before
        defect.closure_image_after = close_data.closure_image_after
        
        system_thread = Thread(
            id=uuid.uuid4(),
            defect_id=defect.id,
            user_id=current_user.id,
            author_role="SYSTEM",
            body=f"✅ Defect CLOSED by {current_user.full_name}. Remarks: {close_data.closure_remarks[:50]}...",
            is_system_message=True
        )
        db.add(system_thread)

        vessel = await db.get(Vessel, defect.vessel_imo)
        vessel_name = vessel.name if vessel else defect.vessel_imo

        await notify_vessel_users(
            db=db,
            vessel_imo=defect.vessel_imo,
            vessel_name=vessel_name,
            title="Defect Closed",
            message=f"Defect '{defect.title}' closed with evidence.",
            exclude_user_id=current_user.id,
            defect_id=str(defect.id)
        )

        await db.commit()
        await db.refresh(defect, attribute_names=["pr_entries"])

        email_data = prepare_email_data(defect)
        background_tasks.add_task(send_defect_email, email_data, "CLOSED")

        return defect
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error closing defect: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- REMOVE DEFECT ---
@router.delete("/{defect_id}")
async def remove_defect(
    defect_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a defect"""
    try:
        defect = await db.get(Defect, defect_id)
        if not defect: 
            raise HTTPException(status_code=404, detail="Defect not found")

        email_data = prepare_email_data(defect)
        
        defect.is_deleted = True 
        await db.commit()

        background_tasks.add_task(send_defect_email, email_data, "REMOVED")

        return {"message": "Defect removed and archived"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error removing defect: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))