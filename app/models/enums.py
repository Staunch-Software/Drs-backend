import enum

class UserRole(str, enum.Enum):
    FLEET_MANAGER = "FLEET_MANAGER"
    SUPERINTENDENT = "SUPERINTENDENT"
    MASTER = "MASTER"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    SECOND_ENGINEER = "SECOND_ENGINEER"

class DefectPriority(str, enum.Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DefectStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"