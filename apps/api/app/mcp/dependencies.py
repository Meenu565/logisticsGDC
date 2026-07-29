from dataclasses import dataclass
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.memory import MemoryService
from app.optimization import RouteOptimizer
from app.providers.routing import OsrmRoutingProvider
from app.recommendations import RecommendationEngine
from app.repositories import (
    AssignmentRepository,
    ConversationRepository,
    DispatchEventRepository,
    DispatchPlanRepository,
    DriverRepository,
    MemorySnapshotRepository,
    OrderRepository,
    RecommendationRepository,
    RouteRepository,
    VehicleRepository,
)
from app.services.business import (
    DispatchEventService,
    DriverAssignmentService,
    DriverService,
    EtaService,
    OrderService,
    PlanningService,
    RecommendationService,
    RouteService,
)


@dataclass
class McpServices:
    db: Session
    orders: OrderService
    drivers: DriverService
    routes: RouteService
    planning: PlanningService
    memory: MemoryService
    recommendations: RecommendationService
    events: DispatchEventService
    plans: DispatchPlanRepository
    assignments: DriverAssignmentService
    eta: EtaService


@contextmanager
def get_mcp_services() -> Iterator[McpServices]:
    db = SessionLocal()
    try:
        event_repository = DispatchEventRepository(db)
        events = DispatchEventService(event_repository)
        order_repository = OrderRepository(db)
        driver_repository = DriverRepository(db)
        vehicle_repository = VehicleRepository(db)
        plan_repository = DispatchPlanRepository(db)
        route_repository = RouteRepository(db)
        recommendation_repository = RecommendationRepository(db)

        yield McpServices(
            db=db,
            orders=OrderService(order_repository, events),
            drivers=DriverService(driver_repository, vehicle_repository, events),
            routes=RouteService(plan_repository, route_repository),
            planning=PlanningService(
                orders=order_repository,
                drivers=driver_repository,
                plans=plan_repository,
                routes=route_repository,
                routing=OsrmRoutingProvider(),
                optimizer=RouteOptimizer(),
            ),
            memory=MemoryService(
                conversations=ConversationRepository(db),
                snapshots=MemorySnapshotRepository(db),
            ),
            recommendations=RecommendationService(
                engine=RecommendationEngine(recommendation_repository),
                plans=plan_repository,
                routes=route_repository,
                drivers=driver_repository,
                recommendations=recommendation_repository,
                events=events,
            ),
            events=events,
            plans=plan_repository,
            assignments=DriverAssignmentService(AssignmentRepository(db), events),
            eta=EtaService(OsrmRoutingProvider()),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
