from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.vessel import Vessel
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash
from app.models.tasks import Task, Notification
from sqlalchemy import update, desc
from app.api.deps import get_current_user # <--- ADDED THIS IMPORT
from uuid import UUID


router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check if Email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail="The user with this email already exists."
        )

    # 2. Fetch the Vessel objects
    vessels_to_assign = []
    if user_in.assigned_vessel_imos:
        # FIX: Use Vessel.imo, not Vessel.imo_number
        stmt = select(Vessel).where(Vessel.imo.in_(user_in.assigned_vessel_imos))
        result = await db.execute(stmt)
        vessels_to_assign = result.scalars().all()

        # Validation: Did we find all ships?
        if len(vessels_to_assign) != len(user_in.assigned_vessel_imos):
            print("⚠️ Warning: Some IMO numbers provided do not exist in DB.")

    # 3. Create User
    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password), # <--- CRITICAL FIX: 'password_hash'
        full_name=user_in.full_name,
        job_title=user_in.job_title,
        role=user_in.role,
        vessels=vessels_to_assign 
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Manually map response to avoid Pydantic validation errors on relationships
    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "is_active": new_user.is_active,
        # Helper to return list of IMOs
        "assigned_vessel_imos": [v.imo for v in new_user.vessels]
    }
# --- TASKS ENDPOINTS ---

@router.get("/me/tasks")
async def get_my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # Auto-identifies Kunal vs Karthik
):
    """Fetch tasks assigned specifically to the logged-in user"""
    stmt = select(Task).where(
        Task.assigned_to_id == current_user.id,
        Task.status == "PENDING"
    ).order_by(desc(Task.created_at))
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a task as done"""
    stmt = update(Task).where(
        Task.id == task_id,
        Task.assigned_to_id == current_user.id
    ).values(status="COMPLETED")
    
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}

# --- NOTIFICATIONS ENDPOINTS ---

@router.get("/me/notifications")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch recent notifications for the user"""
    # Fetch unread first, then new ones
    stmt = select(Notification).where(
        Notification.user_id == current_user.id
    ).order_by(Notification.is_read.asc(), desc(Notification.created_at)).limit(50)
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/notifications/read-all")
async def read_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear the red badge"""
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).values(is_read=True)
    
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}
@router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = update(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).values(is_read=True)
    
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}

# 2. UPDATED: Mark all as SEEN (Opened Bell) - Was previously 'read-all'
@router.patch("/notifications/mark-seen")
async def mark_notifications_seen(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_seen == False
    ).values(is_seen=True)
    
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}