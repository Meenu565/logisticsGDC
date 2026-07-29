from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models import RouteStop, Stop

from app.models import Assignment, DispatchPlan, Route, RouteStop,Stop
from app.repositories.base import Repository


class DispatchPlanRepository(Repository[DispatchPlan]):
    model = DispatchPlan

    def current_for_session(self, session_id: UUID) -> DispatchPlan | None:
        statement = select(DispatchPlan).where(
            DispatchPlan.session_id == session_id,
            DispatchPlan.is_current.is_(True),
        )
        return self.db.scalars(statement).first()

    def set_current(self, session_id: UUID, plan: DispatchPlan) -> DispatchPlan:
        self.db.execute(
            update(DispatchPlan)
            .where(DispatchPlan.session_id == session_id)
            .values(is_current=False)
        )
        plan.is_current = True
        self.db.add(plan)
        self.db.flush()
        return plan

class RouteRepository(Repository[Route]):
    model = Route

    def list_for_plan(self, plan_id: UUID) -> Sequence[Route]:
        return self.db.scalars(select(Route).where(Route.plan_id == plan_id)).all()

    def add_route_stop(self, route_stop: RouteStop) -> RouteStop:
        self.db.add(route_stop)
        self.db.flush()
        return route_stop
    
    def list_route_stops(self, route_id: UUID) -> Sequence[RouteStop]:
        return self.db.scalars(select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.sequence_number)).all()
    
    def get_stop(self, stop_id: UUID) -> Stop | None:
        return self.db.get(Stop, stop_id)



class AssignmentRepository(Repository[Assignment]):
    model = Assignment

    def list_for_plan(self, plan_id: UUID) -> Sequence[Assignment]:
        return self.db.scalars(select(Assignment).where(Assignment.plan_id == plan_id)).all()

    def get_for_plan_order(self, plan_id: UUID, order_id: UUID) -> Assignment | None:
        statement = select(Assignment).where(
            Assignment.plan_id == plan_id,
            Assignment.order_id == order_id,
        )
        return self.db.scalars(statement).first()
