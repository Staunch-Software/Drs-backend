from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.enums import DefectPriority, DefectStatus

# Input Schema: Matches the React formData keys exactly

class VesselUserResponse(BaseModel):
    id: UUID
    full_name: str
    job_title: Optional[str] = None
    
    class Config:
        from_attributes = True

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
    target_close_date: Optional[str] = None 

class DefectCloseRequest(BaseModel):
    closure_remarks: str
    closure_image_before: str
    closure_image_after: str
# Output Schema: What the Shore UI sees
class DefectResponse(BaseModel):
    id: UUID
    vessel_imo: str
    vessel_name: Optional[str] = None
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
    target_close_date: Optional[datetime] = None 
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    closure_remarks: Optional[str] = None
    closure_image_before: Optional[str] = None
    closure_image_after: Optional[str] = None
    
    class Config:
        from_attributes = True

class DefectUpdate(BaseModel):
    equipment: Optional[str] = None
    description: Optional[str] = None
    remarks: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    responsibility: Optional[str] = None
    officeSupport: Optional[str] = None
    prNumber: Optional[str] = None
    prStatus: Optional[str] = None
    
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
    # ✅ FIX: Remove 'alias' here so it accepts "author" from frontend JSON
    author: str 
    body: str
    tagged_user_ids: List[str] = []

class ThreadResponse(BaseModel):
    id: UUID
    defect_id: UUID
    # Output alias is fine (DB 'author_role' -> JSON 'author')
    author: str = Field(alias="author_role") 
    body: str
    created_at: datetime
    user_id: UUID
    is_system_message: bool = False
    tagged_user_ids: List[str] = []
    
    # Use forward reference string or explicit list if AttachmentResponse is defined
    attachments: List['AttachmentResponse'] = [] 

    class Config:
        from_attributes = True
        populate_by_name = True