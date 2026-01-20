import enum

# --- USER ROLES ---
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SHORE = "SHORE"   
    VESSEL= "VESSEL"

# --- VESSEL TYPES ---
class VesselType(str, enum.Enum):
    OIL_TANKER = "OIL_TANKER"
    BULK_CARRIER = "BULK_CARRIER"
    CONTAINER_SHIP = "CONTAINER_SHIP"
    LNG_CARRIER = "LNG_CARRIER"
    GENERAL_CARGO = "GENERAL_CARGO"

# --- DEFECT PRIORITIES ---
# ✅ Added MEDIUM, ensured all are UPPERCASE
class DefectPriority(str, enum.Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"

# --- DEFECT STATUS ---
class DefectStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"