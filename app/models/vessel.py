from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Vessel(Base):
    __tablename__ = "vessels"

    imo_number = Column(String(7), primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    vessel_type = Column(String, nullable=False)
    flag = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    crew = relationship("User", back_populates="vessel")
    defects = relationship("Defect", back_populates="vessel")