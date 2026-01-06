import asyncio
import sys
import os

# Ensure we can import from the 'app' directory
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.user import User
from app.models.vessel import Vessel
# --- CRITICAL FIX: Import Defect so SQLAlchemy registers the relationship ---
from app.models.defect import Defect  
from app.models.enums import UserRole
from app.core.security import get_password_hash

async def seed_database():
    print("🌱 Starting Smart Database Seeding...")
    
    async with SessionLocal() as db:
        try:
            # --- 1. FETCH EXISTING VESSELS ---
            result = await db.execute(select(Vessel))
            existing_vessels = result.scalars().all()

            if not existing_vessels:
                print("❌ No vessels found in Database!")
                print("   Please create a vessel using the API/UI first.")
                return

            print(f"✅ Found {len(existing_vessels)} vessels in the database.")
            
            # Use the first vessel found for the Chief Engineer
            target_vessel = existing_vessels[0] 
            print(f"   ⚓ Will assign Chief Engineer to: {target_vessel.name} (IMO: {target_vessel.imo})")

            # --- 2. SEED USERS ---
            users_data = [
                {
                    "email": "admin@drs.com",
                    "password": "12345",
                    "name": "System Administrator",
                    "role": UserRole.ADMIN,
                    "job": "IT Manager",
                    "assign_vessel": False 
                },
                {
                    "email": "manager@drs.com",
                    "password": "12345",
                    "name": "Capt. James Shore",
                    "role": UserRole.SHORE,
                    "job": "Fleet Manager",
                    "assign_vessel": False
                },
                {
                    "email": "chief@drs.com",
                    "password": "12345",
                    "name": "Chief Eng. Shiva",
                    "role": UserRole.VESSEL,
                    "job": "Chief Engineer",
                    "assign_vessel": True
                }
            ]

            for u_data in users_data:
                # Check if user exists
                stmt = select(User).where(User.email == u_data["email"])
                result = await db.execute(stmt)
                existing_user = result.scalars().first()

                if not existing_user:
                    user = User(
                        email=u_data["email"],
                        password_hash=get_password_hash(u_data["password"]),
                        full_name=u_data["name"],
                        role=u_data["role"],
                        job_title=u_data["job"],
                        is_active=True
                    )

                    # Link to vessel if required
                    if u_data["assign_vessel"]:
                        user.vessels.append(target_vessel)

                    db.add(user)
                    print(f"   👤 Created User: {u_data['email']} ({u_data['role']})")
                else:
                    print(f"   ⚠️ User {u_data['email']} already exists. Skipping.")

            await db.commit()
            print("\n✅ Seeding Complete! Login Credentials:")
            print("------------------------------------------------")
            print("1. ADMIN  : admin@drs.com   / 12345")
            print("2. SHORE  : manager@drs.com / 12345")
            print(f"3. VESSEL : chief@drs.com   / 12345 (Linked to {target_vessel.name})")
            print("------------------------------------------------")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_database())