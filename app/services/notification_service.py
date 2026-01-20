from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.tasks import Notification, NotificationType, Task, TaskStatus
from app.models.user import User
from app.models.vessel import Vessel
from app.models.defect import Defect, DefectStatus

async def notify_vessel_users(
    db: AsyncSession, 
    vessel_imo: str, 
    vessel_name: str,
    title: str, 
    message: str, 
    exclude_user_id: str,
    defect_id: str
):
    # Fetch defect to check status
    defect = await db.get(Defect, defect_id)
    
    stmt = select(User).join(User.vessels).where(
        Vessel.imo == vessel_imo,
        User.id != exclude_user_id,
        User.is_active == True
    )
    result = await db.execute(stmt)
    recipients = result.scalars().all()

    final_message = f"[{vessel_name}] {message}"

    for recipient in recipients:
        # ✅ UPDATED: Route based on BOTH role AND defect status
        if recipient.role == "VESSEL":
            if defect and defect.status == DefectStatus.CLOSED:
                target_link = f"/vessel/closed?highlightDefectId={defect_id}"
            else:
                target_link = f"/vessel/history?highlightDefectId={defect_id}"
        else:  # SHORE/ADMIN
            if defect and defect.status == DefectStatus.CLOSED:
                target_link = f"/shore/history?highlightDefectId={defect_id}"
            else:
                target_link = f"/shore/vessels?highlightDefectId={defect_id}"

        new_notif = Notification(
            user_id=recipient.id,
            type=NotificationType.ALERT,
            title=title,
            message=final_message,
            link=target_link
        )
        db.add(new_notif)

async def create_task_for_mentions(
    db: AsyncSession,
    defect_id: str,
    defect_title: str,
    creator_id: str,
    tagged_user_ids: list[str]
):
    # Fetch defect to check status
    defect = await db.get(Defect, defect_id)
    
    stmt = select(User).where(User.id.in_(tagged_user_ids))
    result = await db.execute(stmt)
    tagged_users = result.scalars().all()

    for user in tagged_users:
        # ✅ UPDATED: Route based on role AND status
        if user.role == "VESSEL":
            if defect and defect.status == DefectStatus.CLOSED:
                target_link = f"/vessel/closed?highlightDefectId={defect_id}"
            else:
                target_link = f"/vessel/history?highlightDefectId={defect_id}"
        else:
            if defect and defect.status == DefectStatus.CLOSED:
                target_link = f"/shore/history?highlightDefectId={defect_id}"
            else:
                target_link = f"/shore/vessels?highlightDefectId={defect_id}"

        task = Task(
            description=f"You were mentioned in: {defect_title}",
            defect_id=defect_id,
            created_by_id=creator_id,
            assigned_to_id=user.id,
            status=TaskStatus.PENDING
        )
        db.add(task)

        notif = Notification(
            user_id=user.id,
            type=NotificationType.MENTION,
            title="New Mention",
            message=f"You were tagged in defect: {defect_title}",
            link=target_link 
        )
        db.add(notif)