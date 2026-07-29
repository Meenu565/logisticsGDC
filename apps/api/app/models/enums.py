from enum import StrEnum


class DriverStatus(StrEnum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_ROUTE = "on_route"
    DELAYED = "delayed"
    OFF_SHIFT = "off_shift"
    UNAVAILABLE = "unavailable"


class VehicleStatus(StrEnum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class OrderStatus(StrEnum):
    NEW = "new"
    PLANNED = "planned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StopKind(StrEnum):
    PICKUP = "pickup"
    DROPOFF = "dropoff"


class RouteStatus(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RecommendationStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"
    UNDONE = "undone"
    EXPIRED = "expired"


class MessageRole(StrEnum):
    DISPATCHER = "dispatcher"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class ImportStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

