import uuid
from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

    # NULL = Shore Staff. NOT NULL = Crew.
    assigned_vessel_imo = Column(String(7), ForeignKey("vessels.imo_number"), nullable=True, index=True)

    # Relationships (Removed Comments)
    vessel = relationship("Vessel", back_populates="crew")
    reported_defects = relationship("Defect", back_populates="reporter")