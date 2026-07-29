from uuid import UUID

from app.repositories.events import DispatchEventRepository
from app.repositories.recommendations import RecommendationRepository
from app.services.business.drivers import DriverService
from app.services.business.orders import OrderService
from app.services.business.routes import RouteService


class DashboardService:
    def __init__(
        self,
        orders: OrderService,
        drivers: DriverService,
        routes: RouteService,
        recommendations: RecommendationRepository,
        events: DispatchEventRepository,
    ) -> None:
        self.orders = orders
        self.drivers = drivers
        self.routes = routes
        self.recommendations = recommendations
        self.events = events
    
         
    def state(self, session_id: UUID) -> dict:
        current_plan = self.routes.current_plan(session_id)
        plan_summary = self.routes.route_summary(current_plan.id) if current_plan else None
        routes = (self.routes.list_routes(current_plan.id)if current_plan else []
    )

        return {
            "session_id": str(session_id),
            "current_plan": plan_summary,
            "routes": self.routes.list_routes(current_plan.id) if current_plan else [],
            "orders": self.orders.list_active_orders(),
            "drivers": self.drivers.list_drivers(),
            "routes": routes,
            "recommendations": self.recommendations.list_open(session_id),
            "timeline": self.events.timeline(session_id),
        }

