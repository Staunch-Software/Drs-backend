import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"

class NotificationType(str, enum.Enum):
    MENTION = "MENTION"        # Tagged in chat
    ALERT = "ALERT"           # Status Change (Open/Close)
    SYSTEM = "SYSTEM"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(String, nullable=False) # e.g. "Review Defect #123"
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Context
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id"))
    
    # Who assigned it? (The person who tagged)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Who is it for? (The person tagged)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who gets this alert?
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    type = Column(Enum(NotificationType), default=NotificationType.SYSTEM)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    link = Column(String) # e.g. "/vessel/dashboard?defectId=..."
    
    is_read = Column(Boolean, default=False)
    is_seen = Column(Boolean, default=False) # Removes from badge (NEW)
    created_at = Column(DateTime, default=datetime.utcnow)