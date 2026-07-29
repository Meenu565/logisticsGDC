from uuid import UUID

from sqlalchemy import delete, select, update

from app.models import (
    Assignment,
    ConversationMessage,
    DispatchEvent,
    DispatchMemorySnapshot,
    DispatchPlan,
    DispatchSession,
    Driver,
    Recommendation,
    RecommendationEvent,
    Route,
    RouteStop,
)
from app.models.enums import DriverStatus
from app.repositories.sessions import DispatchSessionRepository


class DispatchSessionService:
    def __init__(self, sessions: DispatchSessionRepository) -> None:
        self.sessions = sessions

    def create_session(self, title: str = "Dispatch Session") -> DispatchSession:
        return self.sessions.add(DispatchSession(title=title))

    def reset_workspace(self, session_id: UUID) -> DispatchSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        self.clear_planning_state(session_id)
        self.sessions.db.execute(delete(ConversationMessage).where(ConversationMessage.session_id == session_id))
        self.sessions.db.execute(delete(DispatchMemorySnapshot).where(DispatchMemorySnapshot.session_id == session_id))
        self.sessions.db.flush()
        return session

    def clear_planning_state(self, session_id: UUID) -> None:
        plan_ids = list(
            self.sessions.db.scalars(
                select(DispatchPlan.id).where(DispatchPlan.session_id == session_id)
            ).all()
        )
        route_ids = list(
            self.sessions.db.scalars(
                select(Route.id).where(Route.plan_id.in_(plan_ids))
            ).all()
        ) if plan_ids else []
        recommendation_ids = list(
            self.sessions.db.scalars(
                select(Recommendation.id).where(Recommendation.session_id == session_id)
            ).all()
        )

        if recommendation_ids:
            self.sessions.db.execute(
                delete(RecommendationEvent).where(RecommendationEvent.recommendation_id.in_(recommendation_ids))
            )
        self.sessions.db.execute(delete(DispatchEvent).where(DispatchEvent.session_id == session_id))
        self.sessions.db.execute(delete(DispatchMemorySnapshot).where(DispatchMemorySnapshot.session_id == session_id))
        if route_ids:
            self.sessions.db.execute(delete(RouteStop).where(RouteStop.route_id.in_(route_ids)))
        if plan_ids:
            self.sessions.db.execute(delete(Assignment).where(Assignment.plan_id.in_(plan_ids)))
            self.sessions.db.execute(delete(Route).where(Route.plan_id.in_(plan_ids)))
            self.sessions.db.execute(delete(Recommendation).where(Recommendation.session_id == session_id))
            self.sessions.db.execute(delete(DispatchPlan).where(DispatchPlan.id.in_(plan_ids)))
        else:
            self.sessions.db.execute(delete(Recommendation).where(Recommendation.session_id == session_id))

        self.sessions.db.execute(
            update(DispatchSession)
            .where(DispatchSession.id == session_id)
            .values(active_plan_id=None)
        )
        self.sessions.db.execute(
            update(Driver)
            .where(Driver.status == DriverStatus.ASSIGNED)
            .values(status=DriverStatus.AVAILABLE)
        )
        self.sessions.db.flush()
