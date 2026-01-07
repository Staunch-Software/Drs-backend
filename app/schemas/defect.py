from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.enums import DefectPriority, DefectStatus

# Input Schema: Matches the React formData keys exactly
class DefectCreate(BaseModel):
    id: UUID
    vessel_imo: str
    date: Optional[str] = None
    equipment: str
    description: str
    remarks: Optional[str] = None
    priority: str
    status: str
    responsibility: str
    officeSupport: str  # Matches React key
    prNumber: Optional[str] = None
    prStatus: Optional[str] = None
    json_backup_path: Optional[str] = None

# Output Schema: What the Shore UI sees
class DefectResponse(BaseModel):
    id: UUID
    vessel_imo: str
    reported_by_id: UUID
    
    # Include both original and new fields for the response
    title: str
    equipment_name: str
    description: str
    ships_remarks: Optional[str] = None
    priority: DefectPriority
    status: DefectStatus
    office_support_required: bool
    pr_number: Optional[str] = None
    pr_status: Optional[str] = None
    
    # New Phase 1 fields
    responsibility: Optional[str] = None
    json_backup_path: Optional[str] = None
    date_identified: Optional[datetime] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AttachmentBase(BaseModel):
    id: UUID
    thread_id: UUID
    file_name: str
    blob_path: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None

class AttachmentResponse(AttachmentBase):
    created_at: datetime
    class Config:
        from_attributes = True

class ThreadCreate(BaseModel):
    id: UUID
    defect_id: UUID
    author: str
    body: str

class ThreadResponse(BaseModel):
    id: UUID
    defect_id: UUID
    # Map 'author_role' from DB to 'author' in JSON
    author: str = Field(validation_alias="author_role") 
    body: str
    created_at: datetime
    attachments: List[AttachmentResponse] = []
    
    # Pydantic v2 configuration
    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True
    )