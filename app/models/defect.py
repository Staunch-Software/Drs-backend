import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.enums import DefectPriority, DefectStatus
from sqlalchemy.dialects.postgresql import ARRAY

class Defect(Base):
    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True) 
    
    vessel_imo = Column(String(7), ForeignKey("vessels.imo", ondelete="CASCADE"), nullable=False, index=True)
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    equipment_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    ships_remarks = Column(Text, nullable=True)
    priority = Column(Enum(DefectPriority), default=DefectPriority.NORMAL, index=True)
    status = Column(Enum(DefectStatus), default=DefectStatus.OPEN, index=True)
    office_support_required = Column(Boolean, default=False)
    pr_number = Column(String, nullable=True)
    pr_status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    closure_remarks = Column(Text, nullable=True)
    closure_image_before = Column(String, nullable=True) # Azure Blob Path
    closure_image_after = Column(String, nullable=True)  # Azure Blob Path

    responsibility = Column(String, nullable=True)
    json_backup_path = Column(String, nullable=True) # Link to Azure JSON
    date_identified = Column(DateTime, nullable=True) # To store the 'date' from UI
    target_close_date = Column(DateTime, nullable=True) 

    # Relationships
    vessel = relationship("Vessel", back_populates="defects")
    reporter = relationship(
    "User", 
        back_populates="reported_defects", 
        foreign_keys=[reported_by_id] 
    )

    # Explicitly tell SQLAlchemy to use closed_by_id for this link
    closed_by = relationship(
        "User", 
        foreign_keys=[closed_by_id]
    )

class Thread(Base):
    __tablename__ = "threads"
    id = Column(UUID(as_uuid=True), primary_key=True)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id"), nullable=False)
    
    # ADD THIS: Link to the actual user account
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Keep this for the "Display Name" (e.g., "Chief Engineer")
    author_role = Column(String, nullable=False) 
    body = Column(Text, nullable=False)
    tagged_user_ids = Column(ARRAY(String), default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    is_system_message = Column(Boolean, default=False) 

    # Relationships
    defect = relationship("Defect", backref="threads")
    attachments = relationship("Attachment", back_populates="thread")
    user = relationship("User", backref="threads", foreign_keys=[user_id])

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True) # Client-generated
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)
    
    # The path in Azure Blob Storage (Module 3)
    blob_path = Column(String, nullable=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    thread = relationship("Thread", back_populates="attachments")