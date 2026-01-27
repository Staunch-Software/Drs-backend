from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, ARRAY
from sqlalchemy.dialects.postgresql import ENUM  # ✅ Add this import
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.models.enums import DefectPriority, DefectStatus, DefectSource

class Defect(Base):
    __tablename__ = "defects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vessel_imo = Column(String, ForeignKey("vessels.imo"), nullable=False, index=True)
    reported_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Core defect information
    title = Column(String, nullable=False)
    equipment_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # ✅ FIXED: Defect Source - Use values instead of enum names
    defect_source = Column(
        ENUM(
            'Office - Technical',
            'Office - Operation',
            'Internal Audit',
            'External Audit',
            'Third Party - RS',
            'Third Party - PnI',
            'Third Party - Charterer',
            'Third Party - Other',
            "Owner's Inspection",
            name='defectsource',
            create_type=False  # Don't recreate the type
        ),
        nullable=False,
        server_default='Internal Audit'  # Database default
    )    
    # Status and priority
    priority = Column(SQLEnum(DefectPriority, name="defectpriority"), nullable=False)
    status = Column(SQLEnum(DefectStatus, name="defectstatus"), nullable=False)
    responsibility = Column(String, nullable=True)
    pr_status = Column(String, nullable=True, server_default='Not Set')
    # ✅ NEW: Image requirement flags (set by shore side)
    before_image_required = Column(Boolean, default=False, nullable=False)
    after_image_required = Column(Boolean, default=False, nullable=False)
    
    # ✅ NEW: Before/After images uploaded during creation or update
    before_image_path = Column(String, nullable=True)
    after_image_path = Column(String, nullable=True)
    
    # Dates
    date_identified = Column(DateTime(timezone=True), nullable=True)
    target_close_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Closure information
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    closure_remarks = Column(Text, nullable=True)
    closure_image_before = Column(String, nullable=True)
    closure_image_after = Column(String, nullable=True)
    
    # Storage
    json_backup_path = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # ❌ REMOVED: ships_remarks, office_support_required, pr_number, pr_status
    
    # Relationships
    vessel = relationship("Vessel", back_populates="defects")
    reporter = relationship(
    "User",
    foreign_keys=[reported_by_id],
    back_populates="reported_defects"
)

    closed_by = relationship("User", foreign_keys=[closed_by_id])
    threads = relationship("Thread", back_populates="defect", cascade="all, delete-orphan")
    
    # ✅ NEW: One-to-Many relationship with PR entries
    pr_entries = relationship("PrEntry", back_populates="defect", cascade="all, delete-orphan")


class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author_role = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_system_message = Column(Boolean, default=False)
    tagged_user_ids = Column(ARRAY(String), default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    defect = relationship("Defect", back_populates="threads")
    user = relationship("User", foreign_keys=[user_id])
    attachments = relationship("Attachment", back_populates="thread", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)
    blob_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    thread = relationship("Thread", back_populates="attachments")


# ✅ NEW MODEL: PR Entries
class PrEntry(Base):
    __tablename__ = "pr_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False, index=True)
    pr_number = Column(String, nullable=False)
    pr_description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    defect = relationship("Defect", back_populates="pr_entries")
    creator = relationship("User", foreign_keys=[created_by_id])