from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.memory import MemoryService
from app.optimization import RouteOptimizer
from app.providers.routing import OsrmRoutingProvider
from app.recommendations import RecommendationEngine
from app.repositories import (
    AssignmentRepository,
    ConversationRepository,
    DispatchEventRepository,
    DispatchPlanRepository,
    DispatchSessionRepository,
    DriverRepository,
    MemorySnapshotRepository,
    OrderRepository,
    RecommendationRepository,
    RouteRepository,
    VehicleRepository,
)
from app.services.business import (
    DashboardService,
    DispatchEventService,
    DispatchSessionService,
    DriverAssignmentService,
    DriverService,
    EtaService,
    OrderService,
    PlanningService,
    RecommendationService,
    RouteService,
)


@dataclass
class ServiceBundle:
    db: Session
    orders: OrderService
    drivers: DriverService
    routes: RouteService
    planning: PlanningService
    recommendations: RecommendationService
    assignments: DriverAssignmentService
    sessions: DispatchSessionService
    dashboard: DashboardService
    memory: MemoryService
    eta: EtaService
    events: DispatchEventRepository


def get_services(db: Session = Depends(get_db)) -> ServiceBundle:
    event_repository = DispatchEventRepository(db)
    events = DispatchEventService(event_repository)
    order_repository = OrderRepository(db)
    driver_repository = DriverRepository(db)
    vehicle_repository = VehicleRepository(db)
    plan_repository = DispatchPlanRepository(db)
    route_repository = RouteRepository(db)
    recommendation_repository = RecommendationRepository(db)
    routing = OsrmRoutingProvider()

    orders = OrderService(order_repository, events)
    drivers = DriverService(driver_repository, vehicle_repository, events)
    routes = RouteService(plan_repository, route_repository)
    recommendations = RecommendationService(
        engine=RecommendationEngine(recommendation_repository),
        plans=plan_repository,
        routes=route_repository,
        drivers=driver_repository,
        recommendations=recommendation_repository,
        events=events,
    )
    return ServiceBundle(
        db=db,
        orders=orders,
        drivers=drivers,
        routes=routes,
        planning=PlanningService(
            orders=order_repository,
            drivers=driver_repository,
            plans=plan_repository,
            routes=route_repository,
            routing=routing,
            optimizer=RouteOptimizer(),
        ),
        recommendations=recommendations,
        assignments=DriverAssignmentService(AssignmentRepository(db), events),
        sessions=DispatchSessionService(DispatchSessionRepository(db)),
        dashboard=DashboardService(
            orders=orders,
            drivers=drivers,
            routes=routes,
            recommendations=recommendation_repository,
            events=event_repository,
        ),
        memory=MemoryService(
            conversations=ConversationRepository(db),
            snapshots=MemorySnapshotRepository(db),
        ),
        eta=EtaService(routing),
        events=event_repository,
    )

