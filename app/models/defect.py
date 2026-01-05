import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import DefectPriority, DefectStatus

class Defect(Base):
    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- FIX IS HERE ---
    # OLD (Error): ForeignKey("vessels.imo_number")
    # NEW (Correct): ForeignKey("vessels.imo")
    vessel_imo = Column(String(7), ForeignKey("vessels.imo", ondelete="CASCADE"), nullable=False, index=True)
    
    # We also link to the User who reported it
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    title = Column(String, nullable=False)
    equipment = Column(String, nullable=False) # e.g. "Main Engine"
    description = Column(Text)
    
    # Enums are stored as Strings in the DB
    priority = Column(String, default=DefectPriority.NORMAL, nullable=False)
    status = Column(String, default=DefectStatus.OPEN, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Relationships (Optional but useful for API)
    # vessel = relationship("Vessel", back_populates="defects") 
    # reported_by = relationship("User", back_populates="reported_defects")