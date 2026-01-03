from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.enums import DefectPriority, DefectStatus

# Base Schema (Shared properties)
class DefectBase(BaseModel):
    title: str
    equipment_name: str
    description: str
    ships_remarks: Optional[str] = None
    priority: DefectPriority = DefectPriority.NORMAL
    office_support_required: bool = False
    pr_number: Optional[str] = None
    pr_status: Optional[str] = None

# Input Schema (What Frontend sends)
class DefectCreate(DefectBase):
    pass 

# Output Schema (What Backend returns)
class DefectResponse(DefectBase):
    id: UUID
    vessel_imo: str
    reported_by_id: UUID
    status: DefectStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True