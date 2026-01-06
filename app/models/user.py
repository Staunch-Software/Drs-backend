import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import UserRole
from app.models.associations import user_vessel_link # <--- Import the bridge

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    full_name = Column(String, nullable=False)
    job_title = Column(String)  # e.g. "Chief Engineer"
    role = Column(String, default=UserRole.VESSEL, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # RELATIONS
    # This 'secondary' argument is the magic key
    vessels = relationship(
        "Vessel", 
        secondary=user_vessel_link, 
        back_populates="users",
        lazy="selectin"  # HIGH EFFICIENCY: Loads vessels instantly when fetching user
    )

    reported_defects = relationship("Defect", back_populates="reporter")