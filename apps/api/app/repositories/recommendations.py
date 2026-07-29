from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models import Recommendation, RecommendationEvent
from app.models.enums import RecommendationStatus
from app.repositories.base import Repository


class RecommendationRepository(Repository[Recommendation]):
    model = Recommendation

    def list_open(self, session_id: UUID) -> Sequence[Recommendation]:
        statement = select(Recommendation).where(
            Recommendation.session_id == session_id,
            Recommendation.status == RecommendationStatus.PROPOSED,
        )
        return self.db.scalars(statement).all()

    def list_for_session(self, session_id: UUID) -> Sequence[Recommendation]:
        statement = (
            select(Recommendation)
            .where(Recommendation.session_id == session_id)
            .order_by(Recommendation.created_at.desc())
        )
        return self.db.scalars(statement).all()

    def latest_for_session(
        self,
        session_id: UUID,
        status: RecommendationStatus | None = None,
    ) -> Recommendation | None:
        statement = select(Recommendation).where(Recommendation.session_id == session_id)
        if status:
            statement = statement.where(Recommendation.status == status)
        statement = statement.order_by(Recommendation.created_at.desc()).limit(1)
        return self.db.scalars(statement).first()

    def rejected_fingerprint_exists(self, session_id: UUID, fingerprint: str) -> bool:
        statement = select(Recommendation.id).where(
            Recommendation.session_id == session_id,
            Recommendation.status == RecommendationStatus.REJECTED,
            Recommendation.rejection_fingerprint == fingerprint,
        )
        return self.db.scalars(statement).first() is not None

    def open_for_fingerprint(self, session_id: UUID, fingerprint: str) -> Recommendation | None:
        statement = (
            select(Recommendation)
            .where(
                Recommendation.session_id == session_id,
                Recommendation.status == RecommendationStatus.PROPOSED,
                Recommendation.rejection_fingerprint == fingerprint,
            )
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()

    def record_event(
        self,
        recommendation_id: UUID,
        event_type: str,
        details: dict,
    ) -> RecommendationEvent:
        event = RecommendationEvent(
            recommendation_id=recommendation_id,
            event_type=event_type,
            details=details,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def decide(self, recommendation: Recommendation, status: RecommendationStatus) -> Recommendation:
        recommendation.status = status
        recommendation.decided_at = datetime.utcnow()
        self.db.add(recommendation)
        self.db.flush()
        return recommendation
