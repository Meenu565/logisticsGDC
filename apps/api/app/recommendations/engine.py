from uuid import UUID

from app.models import Recommendation
from app.models.enums import RecommendationStatus
from app.recommendations.types import PlanMetrics, RecommendationDraft
from app.repositories.recommendations import RecommendationRepository


class RecommendationEngine:
    def __init__(self, recommendations: RecommendationRepository) -> None:
        self.recommendations = recommendations

    def compare_plans(
        self,
        session_id: UUID,
        current: PlanMetrics,
        proposed: PlanMetrics,
        title: str = "Use optimized dispatch plan",
    ) -> Recommendation | None:
        time_saved = current.total_schedule_seconds - proposed.total_schedule_seconds
        distance_saved = current.total_distance_meters - proposed.total_distance_meters
        if time_saved <= 0 and distance_saved <= 0:
            return None

        fingerprint = f"plan:{current.plan_id}:{proposed.total_distance_meters}:{proposed.total_schedule_seconds}"
        if self.recommendations.rejected_fingerprint_exists(session_id, fingerprint):
            return None
        existing = self.recommendations.open_for_fingerprint(session_id, fingerprint)
        if existing:
            return existing

        benefits: list[str] = []
        if time_saved > 0:
            benefits.append(f"Schedule reduced by {round(time_saved / 60)} minutes.")
        if distance_saved > 0:
            benefits.append(f"Distance reduced by {round(distance_saved / 1000, 1)} km.")

        return self.create(
            session_id=session_id,
            draft=RecommendationDraft(
                title=title,
                reason="The proposed plan improves dispatch efficiency versus the current plan.",
                current_plan_id=current.plan_id,
                proposed_plan_id=proposed.plan_id,
                time_saved_seconds=max(time_saved, 0),
                distance_saved_meters=max(distance_saved, 0),
                operational_benefits=benefits,
                rejection_fingerprint=fingerprint,
            ),
        )

    def create(self, session_id: UUID, draft: RecommendationDraft) -> Recommendation:
        recommendation = Recommendation(
            session_id=session_id,
            current_plan_id=draft.current_plan_id,
            proposed_plan_id=draft.proposed_plan_id,
            title=draft.title,
            reason=draft.reason,
            affected_order_id=draft.affected_order_id,
            from_driver_id=draft.from_driver_id,
            to_driver_id=draft.to_driver_id,
            time_saved_seconds=draft.time_saved_seconds,
            distance_saved_meters=draft.distance_saved_meters,
            operational_benefits=draft.operational_benefits,
            rejection_fingerprint=draft.rejection_fingerprint,
        )
        return self.recommendations.add(recommendation)

    def accept(self, recommendation_id: UUID) -> Recommendation:
        recommendation = self._get_required(recommendation_id)
        updated = self.recommendations.decide(recommendation, RecommendationStatus.ACCEPTED)
        self.recommendations.record_event(recommendation_id, "accepted", {})
        return updated

    def reject(self, recommendation_id: UUID, reason: str | None = None) -> Recommendation:
        recommendation = self._get_required(recommendation_id)
        updated = self.recommendations.decide(recommendation, RecommendationStatus.REJECTED)
        self.recommendations.record_event(recommendation_id, "rejected", {"reason": reason})
        return updated

    def _get_required(self, recommendation_id: UUID) -> Recommendation:
        recommendation = self.recommendations.get(recommendation_id)
        if recommendation is None:
            raise ValueError(f"Recommendation not found: {recommendation_id}")
        return recommendation
