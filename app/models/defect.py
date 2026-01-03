import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import DefectPriority, DefectStatus

class Defect(Base):
    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Links
    vessel_imo = Column(String(7), ForeignKey("vessels.imo_number"), nullable=False, index=True)
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Details
    title = Column(String, nullable=False)
    equipment_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    ships_remarks = Column(Text, nullable=True)
    
    # Status
    priority = Column(Enum(DefectPriority), default=DefectPriority.NORMAL, index=True)
    status = Column(Enum(DefectStatus), default=DefectStatus.OPEN, index=True)
    
    # Logistics
    office_support_required = Column(Boolean, default=False)
    pr_number = Column(String, nullable=True)
    pr_status = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships (Removed Comments)
    vessel = relationship("Vessel", back_populates="defects")
    reporter = relationship("User", back_populates="reported_defects")