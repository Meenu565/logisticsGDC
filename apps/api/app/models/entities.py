from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    DriverStatus,
    ImportStatus,
    MessageRole,
    OrderStatus,
    RecommendationStatus,
    RouteStatus,
    StopKind,
    VehicleStatus,
)


def pg_enum(enum_class, name: str) -> Enum:
    return Enum(
        enum_class,
        name=name,
        values_callable=lambda values: [item.value for item in values],
    )


def uuid_pk() -> Mapped[UUID]:
    return mapped_column(primary_key=True, default=uuid4)


def now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class DeliveryType(Base):
    __tablename__ = "delivery_types"

    id: Mapped[UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dwell_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[UUID] = uuid_pk()
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[DriverStatus] = mapped_column(
        pg_enum(DriverStatus, "driver_status"),
        default=DriverStatus.AVAILABLE,
    )
    max_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_volume_m3: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    shift_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shift_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    home_address_line1: Mapped[str | None] = mapped_column(String)
    home_address_line2: Mapped[str | None] = mapped_column(String)
    home_city: Mapped[str | None] = mapped_column(String)
    home_region: Mapped[str | None] = mapped_column(String)
    home_postal_code: Mapped[str | None] = mapped_column(String)
    home_country: Mapped[str] = mapped_column(String, default="Canada", nullable=False)
    home_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    home_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    current_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    current_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[UUID] = uuid_pk()
    label: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(
        pg_enum(VehicleStatus, "vehicle_status"),
        default=VehicleStatus.AVAILABLE,
    )
    capacity_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_volume_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignments"

    id: Mapped[UUID] = uuid_pk()
    driver_id: Mapped[UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    assigned_at: Mapped[datetime] = now_column()
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_column()


class DriverDeliveryType(Base):
    __tablename__ = "driver_delivery_types"

    driver_id: Mapped[UUID] = mapped_column(ForeignKey("drivers.id"), primary_key=True)
    delivery_type_id: Mapped[UUID] = mapped_column(ForeignKey("delivery_types.id"), primary_key=True)
    is_qualified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = now_column()


class OrderImport(Base):
    __tablename__ = "order_imports"

    id: Mapped[UUID] = uuid_pk()
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        pg_enum(ImportStatus, "import_status"),
        default=ImportStatus.PENDING,
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_column()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = uuid_pk()
    external_order_id: Mapped[str | None] = mapped_column(String, unique=True)
    import_id: Mapped[UUID | None] = mapped_column(ForeignKey("order_imports.id"))
    delivery_type_id: Mapped[UUID] = mapped_column(ForeignKey("delivery_types.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        pg_enum(OrderStatus, "order_status"),
        default=OrderStatus.NEW,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    customer_name: Mapped[str] = mapped_column(String, nullable=False)
    required_weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    required_volume_m3: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    time_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    delivery_type: Mapped[DeliveryType] = relationship()
    stops: Mapped[list["Stop"]] = relationship(back_populates="order")


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    kind: Mapped[StopKind] = mapped_column(pg_enum(StopKind, "stop_kind"), nullable=False)
    address_line1: Mapped[str] = mapped_column(String, nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String)
    city: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str | None] = mapped_column(String)
    postal_code: Mapped[str | None] = mapped_column(String)
    country: Mapped[str] = mapped_column(String, default="Canada", nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    earliest_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latest_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service_minutes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()

    order: Mapped[Order] = relationship(back_populates="stops")


class DispatchSession(Base):
    __tablename__ = "dispatch_sessions"

    id: Mapped[UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String, default="Dispatch Session", nullable=False)
    active_plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("dispatch_plans.id"))
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DispatchPlan(Base):
    __tablename__ = "dispatch_plans"

    id: Mapped[UUID] = uuid_pk()
    session_id: Mapped[UUID] = mapped_column(ForeignKey("dispatch_sessions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String, default="manual", nullable=False)
    total_distance_meters: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_travel_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_dwell_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_schedule_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = now_column()
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[UUID] = uuid_pk()
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("dispatch_plans.id"), nullable=False)
    driver_id: Mapped[UUID | None] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[UUID | None] = mapped_column(ForeignKey("vehicles.id"))
    status: Mapped[RouteStatus] = mapped_column(
        pg_enum(RouteStatus, "route_status"),
        default=RouteStatus.DRAFT,
    )
    route_date: Mapped[date] = mapped_column(Date, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    distance_meters: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    travel_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dwell_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    geometry: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class RouteStop(Base):
    __tablename__ = "route_stops"

    id: Mapped[UUID] = uuid_pk()
    route_id: Mapped[UUID] = mapped_column(ForeignKey("routes.id"), nullable=False)
    stop_id: Mapped[UUID] = mapped_column(ForeignKey("stops.id"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    travel_seconds_from_previous: Mapped[int | None] = mapped_column(Integer)
    distance_meters_from_previous: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[UUID] = uuid_pk()
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("dispatch_plans.id"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    driver_id: Mapped[UUID | None] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[UUID | None] = mapped_column(ForeignKey("vehicles.id"))
    route_id: Mapped[UUID | None] = mapped_column(ForeignKey("routes.id"))
    assigned_at: Mapped[datetime] = now_column()
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = now_column()


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = uuid_pk()
    session_id: Mapped[UUID] = mapped_column(ForeignKey("dispatch_sessions.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(pg_enum(MessageRole, "message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    detected_intent: Mapped[str | None] = mapped_column(String)
    gemini_called: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tool_calls: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = now_column()


class DispatchMemorySnapshot(Base):
    __tablename__ = "dispatch_memory_snapshots"

    id: Mapped[UUID] = uuid_pk()
    session_id: Mapped[UUID] = mapped_column(ForeignKey("dispatch_sessions.id"), nullable=False)
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("dispatch_plans.id"))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = now_column()


class DispatchEvent(Base):
    __tablename__ = "dispatch_events"

    id: Mapped[UUID] = uuid_pk()
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("dispatch_sessions.id"))
    plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("dispatch_plans.id"))
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey("orders.id"))
    driver_id: Mapped[UUID | None] = mapped_column(ForeignKey("drivers.id"))
    vehicle_id: Mapped[UUID | None] = mapped_column(ForeignKey("vehicles.id"))
    recommendation_id: Mapped[UUID | None] = mapped_column(ForeignKey("recommendations.id"))
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = now_column()


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[UUID] = uuid_pk()
    session_id: Mapped[UUID] = mapped_column(ForeignKey("dispatch_sessions.id"), nullable=False)
    current_plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("dispatch_plans.id"))
    proposed_plan_id: Mapped[UUID | None] = mapped_column(ForeignKey("dispatch_plans.id"))
    status: Mapped[RecommendationStatus] = mapped_column(
        pg_enum(RecommendationStatus, "recommendation_status"),
        default=RecommendationStatus.PROPOSED,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    affected_order_id: Mapped[UUID | None] = mapped_column(ForeignKey("orders.id"))
    from_driver_id: Mapped[UUID | None] = mapped_column(ForeignKey("drivers.id"))
    to_driver_id: Mapped[UUID | None] = mapped_column(ForeignKey("drivers.id"))
    time_saved_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distance_saved_meters: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    operational_benefits: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    rejection_fingerprint: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = now_column()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    undone_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    id: Mapped[UUID] = uuid_pk()
    recommendation_id: Mapped[UUID] = mapped_column(ForeignKey("recommendations.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = now_column()
