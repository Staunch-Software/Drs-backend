from pydantic import BaseModel, constr
from datetime import datetime

class VesselBase(BaseModel):
    name: str
    vessel_type: str
    flag: str | None = None

class VesselCreate(VesselBase):
    # VALIDATION: IMO must be exactly 7 digits
    imo_number: constr(min_length=7, max_length=7, pattern=r'^\d{7}$')

class VesselResponse(VesselBase):
    imo_number: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True