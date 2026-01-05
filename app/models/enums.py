import enum

# --- USER ROLES ---
class UserRole(str, enum.Enum):
    CREW = "CREW"
    MASTER = "MASTER"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    SECOND_ENGINEER = "SECOND_ENGINEER"
    SUPERINTENDENT = "SUPERINTENDENT"
    FLEET_MANAGER = "FLEET_MANAGER"
    ADMIN = "ADMIN"

# --- VESSEL TYPES ---
class VesselType(str, enum.Enum):
    OIL_TANKER = "OIL_TANKER"
    BULK_CARRIER = "BULK_CARRIER"
    CONTAINER_SHIP = "CONTAINER_SHIP"
    LNG_CARRIER = "LNG_CARRIER"
    GENERAL_CARGO = "GENERAL_CARGO"

# --- DEFECT PRIORITIES (The Missing Part) ---
class DefectPriority(str, enum.Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# --- DEFECT STATUS (The Missing Part) ---
class DefectStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"