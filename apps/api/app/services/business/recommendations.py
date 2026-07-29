from datetime import datetime
from uuid import UUID

from app.models import Recommendation
from app.models.enums import DriverStatus, RecommendationStatus
from app.recommendations import PlanMetrics, RecommendationDraft, RecommendationEngine
from app.repositories.drivers import DriverRepository
from app.repositories.recommendations import RecommendationRepository
from app.repositories.routes import DispatchPlanRepository
from app.repositories.routes import RouteRepository
from app.services.business.events import DispatchEventService


class RecommendationService:
    def __init__(
        self,
        engine: RecommendationEngine,
        plans: DispatchPlanRepository,
        routes: RouteRepository,
        drivers: DriverRepository,
        recommendations: RecommendationRepository,
        events: DispatchEventService | None = None,
    ) -> None:
        self.engine = engine
        self.plans = plans
        self.routes = routes
        self.drivers = drivers
        self.recommendations = recommendations
        self.events = events

    def generate_for_plans(
        self,
        session_id: UUID,
        current_plan_id: UUID,
        proposed_plan_id: UUID,
    ) -> Recommendation | None:
        current_plan = self.plans.get(current_plan_id)
        proposed_plan = self.plans.get(proposed_plan_id)
        if current_plan is None:
            raise ValueError(f"Current plan not found: {current_plan_id}")
        if proposed_plan is None:
            raise ValueError(f"Proposed plan not found: {proposed_plan_id}")
        return self.engine.compare_plans(
            session_id=session_id,
            current=PlanMetrics(
                plan_id=current_plan.id,
                total_distance_meters=current_plan.total_distance_meters,
                total_travel_seconds=current_plan.total_travel_seconds,
                total_dwell_seconds=current_plan.total_dwell_seconds,
            ),
            proposed=PlanMetrics(
                plan_id=proposed_plan.id,
                total_distance_meters=proposed_plan.total_distance_meters,
                total_travel_seconds=proposed_plan.total_travel_seconds,
                total_dwell_seconds=proposed_plan.total_dwell_seconds,
            ),
        )

    def list_for_session(self, session_id: UUID) -> list[Recommendation]:
        return list(self.recommendations.list_for_session(session_id))

    def expire_open(self, session_id: UUID, keep_id: UUID | None = None) -> None:
        for recommendation in self.recommendations.list_open(session_id):
            if keep_id and recommendation.id == keep_id:
                continue
            recommendation.status = RecommendationStatus.EXPIRED
            recommendation.decided_at = datetime.utcnow()
            self.recommendations.add(recommendation)

    def create_strategy_recommendation(
        self,
        session_id: UUID,
        strategy: str,
        proposed_plan_id: UUID,
        current_plan_id: UUID | None,
        vehicles_used: int,
        orders_covered: int,
        unassigned_orders: list[str],
        capacity_notes: list[str],
        scheduling_notes: list[str],
        pros: list[str],
        cons: list[str],
        why_recommended: str,
    ) -> Recommendation:
        proposed_plan = self.plans.get(proposed_plan_id)
        if proposed_plan is None:
            raise ValueError(f"Proposed plan not found: {proposed_plan_id}")
        current_plan = self.plans.get(current_plan_id) if current_plan_id else None
        time_saved = (
            current_plan.total_schedule_seconds - proposed_plan.total_schedule_seconds
            if current_plan
            else 0
        )
        distance_saved = (
            current_plan.total_distance_meters - proposed_plan.total_distance_meters
            if current_plan
            else 0
        )
        fuel_savings_liters = max(distance_saved, 0) / 1000 * 0.12
        fingerprint = (
            f"strategy:{strategy}:{session_id}:"
            f"{proposed_plan.total_distance_meters}:{proposed_plan.total_schedule_seconds}:{orders_covered}"
        )
        existing = self.recommendations.open_for_fingerprint(session_id, fingerprint)
        if existing:
            return existing

        operational_benefits = [
            f"Strategy: {strategy}",
            f"Estimated distance: {round(proposed_plan.total_distance_meters / 1000, 1)} km",
            f"Estimated travel time: {round(proposed_plan.total_travel_seconds / 60)} minutes",
            f"Estimated fuel savings: {round(fuel_savings_liters, 1)} liters" if fuel_savings_liters else "Estimated fuel savings: unavailable until there is a current baseline plan",
            f"Vehicles used: {vehicles_used}",
            f"Orders covered: {orders_covered}",
            *[f"Pros: {item}" for item in pros],
            *[f"Cons: {item}" for item in cons],
            f"AI recommendation: {why_recommended}",
        ]
        if unassigned_orders:
            operational_benefits.append(f"Unassigned orders: {', '.join(unassigned_orders[:6])}")
        operational_benefits.extend(f"Capacity: {item}" for item in capacity_notes[:6])
        operational_benefits.extend(f"Scheduling: {item}" for item in scheduling_notes[:6])

        return self.engine.create(
            session_id=session_id,
            draft=RecommendationDraft(
                title=f"{strategy} dispatch strategy",
                reason=self._strategy_reason(
                    strategy=strategy,
                    vehicles_used=vehicles_used,
                    orders_covered=orders_covered,
                    unassigned_orders=unassigned_orders,
                    why_recommended=why_recommended,
                ),
                current_plan_id=current_plan_id,
                proposed_plan_id=proposed_plan_id,
                time_saved_seconds=max(time_saved, 0),
                distance_saved_meters=max(distance_saved, 0),
                operational_benefits=operational_benefits,
                rejection_fingerprint=fingerprint,
            ),
        )

    def accept(self, recommendation_id: UUID, session_id: UUID | None = None) -> Recommendation:
        existing = self.engine._get_required(recommendation_id)
        if existing.status == RecommendationStatus.APPLIED:
            return existing
        recommendation = self.engine.accept(recommendation_id)
        if self.events:
            self.events.record(
                event_type="recommendation_accepted",
                title=recommendation.title,
                details={"recommendation_id": str(recommendation.id)},
                session_id=session_id or recommendation.session_id,
                recommendation_id=recommendation.id,
            )
        return recommendation

    def apply(self, recommendation_id: UUID, session_id: UUID) -> Recommendation:
        recommendation = self.engine._get_required(recommendation_id)
        if recommendation.status == RecommendationStatus.APPLIED:
            return recommendation
        if recommendation.status != RecommendationStatus.ACCEPTED:
            raise ValueError("Recommendation must be accepted before it can be applied.")
        recommendation.status = RecommendationStatus.APPLIED
        recommendation.applied_at = datetime.utcnow()
        if recommendation.proposed_plan_id:
            plan = self.plans.get(recommendation.proposed_plan_id)
            if plan:
                self.plans.set_current(session_id, plan)
                self._mark_route_drivers_assigned(plan.id)
        self.expire_open(session_id, keep_id=recommendation.id)
        self.engine.recommendations.add(recommendation)
        self.engine.recommendations.record_event(recommendation_id, "applied", {})
        if self.events:
            self.events.record(
                event_type="recommendation_applied",
                title=recommendation.title,
                details={"recommendation_id": str(recommendation.id)},
                session_id=session_id,
                recommendation_id=recommendation.id,
            )
        return recommendation

    def reject(self, recommendation_id: UUID, reason: str | None = None) -> Recommendation:
        recommendation = self.engine.reject(recommendation_id, reason)
        if self.events:
            self.events.record(
                event_type="recommendation_rejected",
                title=recommendation.title,
                details={"recommendation_id": str(recommendation.id), "reason": reason},
                session_id=recommendation.session_id,
                recommendation_id=recommendation.id,
            )
        return recommendation

    def undo_last_applied(self, session_id: UUID) -> Recommendation:
        recommendation = self.recommendations.latest_for_session(
            session_id,
            status=RecommendationStatus.APPLIED,
        )
        if recommendation is None:
            raise ValueError("No applied recommendation found to undo.")
        if recommendation.current_plan_id:
            previous_plan = self.plans.get(recommendation.current_plan_id)
            if previous_plan:
                self.plans.set_current(session_id, previous_plan)
                self._mark_route_drivers_assigned(previous_plan.id)
        recommendation.status = RecommendationStatus.UNDONE
        recommendation.undone_at = datetime.utcnow()
        self.engine.recommendations.add(recommendation)
        self.engine.recommendations.record_event(recommendation.id, "undone", {})
        if self.events:
            self.events.record(
                event_type="recommendation_undone",
                title=f"Undid: {recommendation.title}",
                details={"recommendation_id": str(recommendation.id)},
                session_id=session_id,
                recommendation_id=recommendation.id,
            )
        return recommendation

    def _mark_route_drivers_assigned(self, plan_id: UUID) -> None:
        for route in self.routes.list_for_plan(plan_id):
            if route.driver_id:
                driver = self.drivers.get(route.driver_id)
                if driver:
                    driver.status = DriverStatus.ASSIGNED
                    self.drivers.save(driver)

    def _strategy_reason(
        self,
        strategy: str,
        vehicles_used: int,
        orders_covered: int,
        unassigned_orders: list[str],
        why_recommended: str,
    ) -> str:
        unassigned = (
            f" {len(unassigned_orders)} orders remain unassigned because of capacity, location, or schedule constraints."
            if unassigned_orders
            else " All eligible orders fit within available vehicle capacity and schedule checks."
        )
        return (
            f"{strategy} covers {orders_covered} orders across {vehicles_used} vehicles. "
            f"{why_recommended}{unassigned}"
        )
