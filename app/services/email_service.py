import os
import re
from pathlib import Path
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import SessionLocal
from app.models.user import User
from app.models.vessel import Vessel
from app.models.enums import UserRole
from dotenv import load_dotenv

# Force load .env to ensure we get the latest changes
load_dotenv()

# 1. Define Path to Template
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_FOLDER = Path(BASE_DIR, "templates")

print(f"📂 Template Folder: {TEMPLATE_FOLDER}")
print(f"📧 Configuring Mail Server: {os.getenv('MAIL_SERVER')}:{os.getenv('MAIL_PORT')}")

# 2. Configure Connection
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Maritime DRS"),
    
    # --- CRITICAL SETTINGS FOR LOCALHOST ---
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    
    # SET THIS TO FALSE FOR LOCALHOST / PRIVATE SERVERS
    # It prevents "Certificate Verify Failed" errors
    VALIDATE_CERTS=False, 
    
    TEMPLATE_FOLDER=str(TEMPLATE_FOLDER)
)

def is_valid_email(email: str) -> bool:
    if not email: return False
    # Basic Regex
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email): return False
    # Filter mock
    if email.split('@')[-1] in ["example.com", "test.com", "localhost"]: return False
    return True

async def get_recipients_for_vessel(vessel_imo: str) -> List[str]:
    recipients = set()
    
    async with SessionLocal() as db:
        # A. Get Linked Users (Captain, etc.)
        stmt_vessel = select(Vessel).where(Vessel.imo == vessel_imo).options(selectinload(Vessel.users))
        result_vessel = await db.execute(stmt_vessel)
        vessel = result_vessel.scalars().first()
        
        if vessel:
            if is_valid_email(vessel.email): recipients.add(vessel.email)
            for user in vessel.users:
                if is_valid_email(user.email) and user.is_active:
                    recipients.add(user.email)

        # B. Get Admin/Shore Users (Fixed Enum Logic)
        target_roles = []
        if hasattr(UserRole.ADMIN, 'value'):
            target_roles = [UserRole.ADMIN.value, UserRole.SHORE.value]
        else:
            target_roles = ["ADMIN", "SHORE"]

        stmt_admins = select(User).where(User.role.in_(target_roles), User.is_active == True)
        result_admins = await db.execute(stmt_admins)
        admins = result_admins.scalars().all()
        
        for admin in admins:
            if is_valid_email(admin.email): recipients.add(admin.email)
    
    final_list = list(recipients)
    print(f"🎯 Email Targets for {vessel_imo}: {final_list}")
    return final_list

async def send_defect_email(defect_data: dict, event_type: str):
    print(f"🚀 Attempting to send email via {conf.MAIL_SERVER}...")
    
    recipients = await get_recipients_for_vessel(defect_data['vessel_imo'])
    
    if not recipients:
        print("⚠️ No recipients found. Email skipped.")
        return

    defect_data["event_type"] = event_type
    template_name = "defect_notification.html"
    
    subject_map = {
        "CREATED": f"🚨 New Defect: {defect_data['title']}",
        "UPDATED": f"📝 Defect Updated: {defect_data['title']}",
        "CLOSED": f"✅ Defect Closed: {defect_data['title']}"
    }

    message = MessageSchema(
        subject=f"[{defect_data['vessel_imo']}] {subject_map.get(event_type)}",
        recipients=recipients,
        template_body=defect_data,
        subtype=MessageType.html
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
        print(f"✅ Email SUCCESSFULLY sent via {conf.MAIL_SERVER}")
    except Exception as e:
        print(f"❌ Email Failed. Check your .env settings!")
        print(f"   Server Response: {str(e)}")