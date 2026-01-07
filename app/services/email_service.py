import os
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.models.vessel import Vessel
from app.models.enums import UserRole

# 1. Configure Connection
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=os.path.join(os.getcwd(), 'app/templates/email') # Folder for HTML
)

async def get_recipients_for_vessel(vessel_imo: str) -> List[str]:
    """
    Finds all SHORE managers and ADMINS linked to this vessel.
    """
    recipients = []
    async with SessionLocal() as db:
        # Get the Vessel and its Linked Users
        stmt = select(Vessel).where(Vessel.imo == vessel_imo).options(selectinload(Vessel.users))
        result = await db.execute(stmt)
        vessel = result.scalars().first()
        
        if vessel:
            # Filter users: Only send to SHORE or ADMIN
            for user in vessel.users:
                if user.role in [UserRole.SHORE, UserRole.ADMIN] and user.email:
                    recipients.append(user.email)
                    
            # Optional: Add the ship's own email if it exists
            if vessel.email:
                recipients.append(vessel.email)
                
    return list(set(recipients)) # Remove duplicates

async def send_defect_email(defect_data: dict, event_type: str):
    """
    Main function to send email. 
    event_type: "CREATED", "UPDATED", "CLOSED"
    """
    # 1. Get Recipients
    recipients = await get_recipients_for_vessel(defect_data['vessel_imo'])
    
    if not recipients:
        print("⚠️ No recipients found for email notification.")
        return

    # 2. Select Template
    template_name = "defect_notification.html"
    
    subject_map = {
        "CREATED": f"🚨 New Defect: {defect_data['title']}",
        "UPDATED": f"📝 Defect Updated: {defect_data['title']}",
        "CLOSED": f"✅ Defect Closed: {defect_data['title']}"
    }

    subject = subject_map.get(event_type, "DRS Notification")

    # 3. Prepare Message
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=defect_data, # Pass data to HTML
        subtype=MessageType.html
    )

    # 4. Send
    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)
    print(f"📧 Email sent to {len(recipients)} recipients for Defect {defect_data['title']}")