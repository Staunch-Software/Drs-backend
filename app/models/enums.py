from enum import Enum

class UserRole(str, Enum):
    VESSEL = "VESSEL"
    SHORE = "SHORE"
    ADMIN = "ADMIN"

class DefectPriority(str, Enum):
    NORMAL = "NORMAL"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DefectStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

class DefectSource(str, Enum):
    OFFICE_TECHNICAL = "Office - Technical"
    OFFICE_OPERATION = "Office - Operation"
    INTERNAL_AUDIT = "Internal Audit"
    EXTERNAL_AUDIT = "External Audit"
    THIRD_PARTY_RS = "Third Party - RS"
    THIRD_PARTY_PNI = "Third Party - PnI"
    THIRD_PARTY_CHARTERER = "Third Party - Charterer"
    THIRD_PARTY_OTHER = "Third Party - Other"
    OWNERS_INSPECTION = "Owner's Inspection"

class VesselType(str, Enum):
    OIL_TANKER = "OIL_TANKER"
    BULK_CARRIER = "BULK_CARRIER"
    CONTAINER_SHIP = "CONTAINER_SHIP"
    LNG_CARRIER = "LNG_CARRIER"
    GENERAL_CARGO = "GENERAL_CARGO"