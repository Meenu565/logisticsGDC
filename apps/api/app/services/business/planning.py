from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from app.models import DispatchPlan, Route, RouteStop, Vehicle
from app.optimization import PlanningDriver, PlanningStop, RouteOptimizer, coordinates_for_problem
from app.providers.routing import RoutingProvider
from app.repositories.drivers import DriverRepository
from app.repositories.orders import OrderRepository
from app.repositories.routes import DispatchPlanRepository, RouteRepository


@dataclass(frozen=True)
class OptimizationStrategyPlan:
    strategy: str
    plan: DispatchPlan
    vehicles_used: int
    orders_covered: int
    unassigned_orders: list[str]
    capacity_notes: list[str]
    scheduling_notes: list[str]
    pros: list[str]
    cons: list[str]
    why_recommended: str


@dataclass
class RouteBuildState:
    driver: PlanningDriver
    driver_name: str
    vehicle_label: str
    remaining_weight: float | None
    remaining_volume: float | None
    previous_node: int
    elapsed_seconds: int = 0
    driving_seconds: int = 0
    distance_meters: int = 0
    dwell_seconds: int = 0
    stops: list[tuple[PlanningStop, int, int, datetime | None, datetime | None]] = None

    def __post_init__(self) -> None:
        if self.stops is None:
            self.stops = []


class PlanningService:
    def __init__(
        self,
        orders: OrderRepository,
        drivers: DriverRepository,
        plans: DispatchPlanRepository,
        routes: RouteRepository,
        routing: RoutingProvider,
        optimizer: RouteOptimizer,
    ) -> None:
        self.orders = orders
        self.drivers = drivers
        self.plans = plans
        self.routes = routes
        self.routing = routing
        self.optimizer = optimizer

    def optimize_routes(
        self,
        session_id: UUID,
        route_date: date,
        order_ids: list[UUID] | None = None,
    ) -> DispatchPlan:
        plan = self._build_plan(
            session_id=session_id,
            route_date=route_date,
            order_ids=order_ids,
            name=f"Optimized plan for {route_date.isoformat()}",
            source_suffix="balanced",
            set_current=True,
        )
        return plan

    def optimize_route_strategies(
        self,
        session_id: UUID,
        route_date: date,
        order_ids: list[UUID] | None = None,
    ) -> list[OptimizationStrategyPlan]:
        strategies = [
            (
                "Fastest Route",
                "fastest",
                "Prioritizes tighter time windows and higher-priority deliveries for quickest completion.",
                ["Best choice when service windows and completion time matter most."],
                ["May use slightly more distance if it protects arrival times."],
            ),
            (
                "Shortest Route",
                "shortest",
                "Clusters stops geographically to reduce total travel distance and fuel burn.",
                ["Reduces mileage and fuel exposure where coordinates allow clustering."],
                ["May not be the fastest if priority or time windows are tight."],
            ),
            (
                "Balanced Route",
                "balanced",
                "Balances travel time, distance, workload, available capacity, and route duration.",
                ["Best overall dispatch plan when time, capacity, and workload all matter."],
                ["May not be the absolute fastest or shortest single metric plan."],
            ),
        ]

        plans: list[OptimizationStrategyPlan] = []
        for strategy, source_suffix, why, pros, cons in strategies:
            plan, capacity_notes, scheduling_notes, unassigned_orders = self._build_plan_with_notes(
                session_id=session_id,
                route_date=route_date,
                order_ids=order_ids,
                name=f"{strategy} plan for {route_date.isoformat()}",
                source_suffix=source_suffix,
                set_current=False,
            )
            plans.append(
                OptimizationStrategyPlan(
                    strategy=strategy,
                    plan=plan,
                    vehicles_used=sum(1 for route in self.routes.list_for_plan(plan.id) if self.routes.list_route_stops(route.id)),
                    orders_covered=sum(
                        len(self.routes.list_route_stops(route.id))
                        for route in self.routes.list_for_plan(plan.id)
                    ),
                    unassigned_orders=unassigned_orders,
                    capacity_notes=capacity_notes,
                    scheduling_notes=scheduling_notes,
                    pros=pros,
                    cons=cons,
                    why_recommended=why,
                )
            )
        return plans

    def _build_plan(
        self,
        session_id: UUID,
        route_date: date,
        order_ids: list[UUID] | None,
        name: str,
        source_suffix: str,
        set_current: bool,
    ) -> DispatchPlan:
        plan, _, _, _ = self._build_plan_with_notes(
            session_id=session_id,
            route_date=route_date,
            order_ids=order_ids,
            name=name,
            source_suffix=source_suffix,
            set_current=set_current,
        )
        return plan

    def _build_plan_with_notes(
        self,
        session_id: UUID,
        route_date: date,
        order_ids: list[UUID] | None,
        name: str,
        source_suffix: str,
        set_current: bool,
    ) -> tuple[DispatchPlan, list[str], list[str], list[str]]:
        orders = list(self.orders.list_by_ids(order_ids)) if order_ids else list(self.orders.list_active())
        orders = self._sort_orders_for_strategy(orders, source_suffix)
        available_drivers = self._sort_drivers_for_strategy(list(self.drivers.list_eligible_for_planning()), source_suffix)

        planning_drivers: list[PlanningDriver] = []
        driver_names: dict[UUID, str] = {}
        vehicle_labels: dict[UUID, str] = {}
        availability_notes: list[str] = []
        for driver in available_drivers:
            shift_start = self._effective_shift_start(driver, route_date)
            shift_end = self._effective_shift_end(driver, route_date, shift_start)
            if shift_start and shift_end and shift_end <= shift_start:
                availability_notes.append(f"{driver.display_name} was skipped because their shift timing is invalid.")
                continue
            vehicle_assignment = self.drivers.current_vehicle_assignment(driver.id)
            vehicle = self.drivers.db.get(Vehicle, vehicle_assignment.vehicle_id) if vehicle_assignment else None
            planning_drivers.append(
                PlanningDriver(
                    driver_id=driver.id,
                    vehicle_id=vehicle_assignment.vehicle_id if vehicle_assignment else None,
                    start_latitude=float(driver.current_latitude or driver.home_latitude or Decimal("0")),
                    start_longitude=float(driver.current_longitude or driver.home_longitude or Decimal("0")),
                    max_weight_kg=self._vehicle_weight_capacity(driver, vehicle),
                    max_volume_m3=self._vehicle_volume_capacity(driver, vehicle),
                    shift_start=shift_start,
                    shift_end=shift_end,
                )
            )
            driver_names[driver.id] = driver.display_name
            vehicle_labels[driver.id] = vehicle.label if vehicle else "Unassigned truck"

        planning_stops: list[PlanningStop] = []
        order_labels: dict[UUID, str] = {}
        for order in orders:
            order_labels[order.id] = order.external_order_id or order.customer_name
            dropoff = next((stop for stop in order.stops if stop.kind.value == "dropoff"), None)
            if dropoff is None or dropoff.latitude is None or dropoff.longitude is None:
                continue
            dwell_minutes = dropoff.service_minutes or order.delivery_type.dwell_minutes
            planning_stops.append(
                PlanningStop(
                    order_id=order.id,
                    stop_id=dropoff.id,
                    weight_kg=float(order.required_weight_kg),
                    volume_m3=float(order.required_volume_m3),
                    latitude=float(dropoff.latitude),
                    longitude=float(dropoff.longitude),
                    dwell_seconds=dwell_minutes * 60,
                    priority=order.priority,
                    earliest_at=dropoff.earliest_at or order.time_window_start,
                    latest_at=dropoff.latest_at or order.time_window_end,
                )
            )

        coordinates = coordinates_for_problem(planning_drivers, planning_stops)
        matrix = self.routing.matrix(coordinates)

        plan = DispatchPlan(
            session_id=session_id,
            name=name,
            source=f"matrix_dispatch:{source_suffix}",
            total_distance_meters=0,
            total_travel_seconds=0,
            total_dwell_seconds=0,
            total_schedule_seconds=0,
        )
        self.plans.add(plan)

        capacity_notes: list[str] = []
        scheduling_notes: list[str] = availability_notes
        unassigned_stop_ids: set[UUID] = set()
        assigned_order_ids: set[UUID] = set()
        totals = {"distance": 0, "travel": 0, "dwell": 0}

        route_states = [
            RouteBuildState(
                driver=driver,
                driver_name=driver_names.get(driver.driver_id, "Driver"),
                vehicle_label=vehicle_labels.get(driver.driver_id, "Unassigned truck"),
                remaining_weight=driver.max_weight_kg,
                remaining_volume=driver.max_volume_m3,
                previous_node=index,
            )
            for index, driver in enumerate(planning_drivers)
        ]
        stop_nodes = {stop.stop_id: len(planning_drivers) + index for index, stop in enumerate(planning_stops)}

        for stop in planning_stops:
            assignment = self._best_feasible_assignment(
                stop=stop,
                states=route_states,
                stop_node=stop_nodes[stop.stop_id],
                matrix=matrix,
                route_date=route_date,
                strategy=source_suffix,
            )
            if assignment is None:
                unassigned_stop_ids.add(stop.stop_id)
                reasons = self._rejection_reasons(stop, route_states, stop_nodes[stop.stop_id], matrix, route_date)
                capacity_notes.extend(
                    reason for reason in reasons if "capacity" in reason.lower() or "truck" in reason.lower()
                )
                scheduling_notes.extend(
                    reason for reason in reasons if "shift" in reason.lower() or "window" in reason.lower() or "driver" in reason.lower()
                )
                if not any(
                    "capacity" in reason.lower()
                    or "truck" in reason.lower()
                    or "shift" in reason.lower()
                    or "window" in reason.lower()
                    or "driver" in reason.lower()
                    for reason in reasons
                ):
                    scheduling_notes.extend(reasons)
                continue
            state, leg_seconds, leg_distance, arrival, departure = assignment
            state.remaining_weight = None if state.remaining_weight is None else state.remaining_weight - stop.weight_kg
            state.remaining_volume = None if state.remaining_volume is None else state.remaining_volume - stop.volume_m3
            state.previous_node = stop_nodes[stop.stop_id]
            state.elapsed_seconds = self._elapsed_after_departure(state.driver, route_date, departure, state.elapsed_seconds + leg_seconds + stop.dwell_seconds)
            state.driving_seconds += leg_seconds
            state.distance_meters += leg_distance
            state.dwell_seconds += stop.dwell_seconds
            state.stops.append((stop, leg_seconds, leg_distance, arrival, departure))
            assigned_order_ids.add(stop.order_id)
            capacity_notes.append(
                f"{order_labels.get(stop.order_id, 'Order')} assigned to {state.driver_name} on {state.vehicle_label}; remaining capacity is {self._capacity_text(state.remaining_weight, state.remaining_volume)}."
            )
            if arrival:
                scheduling_notes.append(
                    f"{order_labels.get(stop.order_id, 'Order')} scheduled for {state.driver_name} at {arrival.strftime('%H:%M')}."
                )

        for state in route_states:
            if not state.stops:
                continue
            route = self.routes.add(
                Route(
                    plan_id=plan.id,
                    driver_id=state.driver.driver_id,
                    vehicle_id=state.driver.vehicle_id,
                    route_date=route_date,
                    starts_at=state.driver.shift_start,
                    distance_meters=state.distance_meters,
                    travel_seconds=state.driving_seconds,
                    dwell_seconds=state.dwell_seconds,
                )
            )
            for sequence, (stop, leg_seconds, leg_distance, arrival, departure) in enumerate(state.stops, start=1):
                self.routes.add_route_stop(
                    RouteStop(
                        route_id=route.id,
                        stop_id=stop.stop_id,
                        sequence_number=sequence,
                        planned_arrival_at=arrival,
                        planned_departure_at=departure,
                        travel_seconds_from_previous=leg_seconds,
                        distance_meters_from_previous=leg_distance,
                    )
                )
            route.ends_at = state.driver.shift_start + timedelta(seconds=state.elapsed_seconds) if state.driver.shift_start else None
            totals["distance"] += state.distance_meters
            totals["travel"] += state.driving_seconds
            totals["dwell"] += state.dwell_seconds

        plan.total_distance_meters = totals["distance"]
        plan.total_travel_seconds = totals["travel"]
        plan.total_dwell_seconds = totals["dwell"]
        plan.total_schedule_seconds = sum(state.elapsed_seconds for state in route_states)
        self.plans.add(plan)
        if set_current:
            self.plans.set_current(session_id, plan)

        unassigned_orders = [
            order_labels.get(stop.order_id, str(stop.order_id))
            for stop in planning_stops
            if stop.stop_id in unassigned_stop_ids or stop.order_id not in assigned_order_ids
        ]
        return plan, capacity_notes, scheduling_notes, unassigned_orders

    def _fits_capacity(
        self,
        stop: PlanningStop,
        remaining_weight: float | None,
        remaining_volume: float | None,
    ) -> bool:
        if remaining_weight is not None and stop.weight_kg > remaining_weight:
            return False
        if remaining_volume is not None and stop.volume_m3 > remaining_volume:
            return False
        return True

    def _best_feasible_assignment(
        self,
        stop: PlanningStop,
        states: list[RouteBuildState],
        stop_node: int,
        matrix,
        route_date: date,
        strategy: str,
    ) -> tuple[RouteBuildState, int, int, datetime | None, datetime | None] | None:
        candidates: list[tuple[float, RouteBuildState, int, int, datetime | None, datetime | None]] = []
        for state in states:
            if not self._fits_capacity(stop, state.remaining_weight, state.remaining_volume):
                continue
            leg_seconds = matrix.durations_seconds[state.previous_node][stop_node]
            leg_distance = matrix.distances_meters[state.previous_node][stop_node]
            arrival, departure, projected_elapsed = self._project_timing(
                state=state,
                stop=stop,
                route_date=route_date,
                leg_seconds=leg_seconds,
            )
            if not self._within_time_window(stop, arrival):
                continue
            if state.driver.shift_end and departure and departure > state.driver.shift_end:
                continue
            if strategy == "shortest":
                score = leg_distance
            elif strategy == "balanced":
                score = projected_elapsed + (len(state.stops) * 900) + (leg_distance * 0.15)
            else:
                score = projected_elapsed
            candidates.append((score, state, leg_seconds, leg_distance, arrival, departure))
        if not candidates:
            return None
        _, state, leg_seconds, leg_distance, arrival, departure = min(candidates, key=lambda item: item[0])
        return state, leg_seconds, leg_distance, arrival, departure

    def _rejection_reasons(
        self,
        stop: PlanningStop,
        states: list[RouteBuildState],
        stop_node: int,
        matrix,
        route_date: date,
    ) -> list[str]:
        if not states:
            return ["No available driver/truck can take this order."]
        reasons: list[str] = []
        capacity_failed = True
        time_failed = False
        shift_failed = False
        for state in states:
            if self._fits_capacity(stop, state.remaining_weight, state.remaining_volume):
                capacity_failed = False
            leg_seconds = matrix.durations_seconds[state.previous_node][stop_node]
            arrival, departure, _ = self._project_timing(
                state=state,
                stop=stop,
                route_date=route_date,
                leg_seconds=leg_seconds,
            )
            if not self._within_time_window(stop, arrival):
                time_failed = True
            if state.driver.shift_end and departure and departure > state.driver.shift_end:
                shift_failed = True
        if capacity_failed:
            reasons.append(
                f"Truck capacity blocked the order: it requires {round(stop.weight_kg, 1)} kg and {round(stop.volume_m3, 2)} m3."
            )
        if time_failed:
            reasons.append("Customer time window blocked the order for the available route options.")
        if shift_failed:
            reasons.append("Driver shift end time blocked the order for the available route options.")
        return reasons or ["No feasible driver/truck combination was found for this order."]

    def _project_timing(
        self,
        state: RouteBuildState,
        stop: PlanningStop,
        route_date: date,
        leg_seconds: int,
    ) -> tuple[datetime | None, datetime | None, int]:
        projected_elapsed = state.elapsed_seconds + leg_seconds
        start = state.driver.shift_start or datetime.combine(route_date, time(hour=8))
        arrival = start + timedelta(seconds=projected_elapsed)
        if stop.earliest_at and arrival < stop.earliest_at:
            arrival = stop.earliest_at
            projected_elapsed = int((arrival - start).total_seconds())
        departure = arrival + timedelta(seconds=stop.dwell_seconds)
        projected_elapsed = int((departure - start).total_seconds())
        return arrival, departure, projected_elapsed

    def _elapsed_after_departure(
        self,
        driver: PlanningDriver,
        route_date: date,
        departure: datetime | None,
        fallback_elapsed: int,
    ) -> int:
        if not departure:
            return fallback_elapsed
        start = driver.shift_start or datetime.combine(route_date, time(hour=8))
        return int((departure - start).total_seconds())

    def _within_time_window(self, stop: PlanningStop, arrival: datetime | None) -> bool:
        if not arrival:
            return True
        if stop.latest_at and arrival > stop.latest_at:
            return False
        return True

    def _effective_shift_start(self, driver, route_date: date) -> datetime | None:
        if not driver.shift_start:
            return None
        return datetime.combine(route_date, driver.shift_start.timetz().replace(tzinfo=driver.shift_start.tzinfo))

    def _effective_shift_end(self, driver, route_date: date, shift_start: datetime | None) -> datetime | None:
        if not driver.shift_end:
            return None
        shift_end = datetime.combine(route_date, driver.shift_end.timetz().replace(tzinfo=driver.shift_end.tzinfo))
        if shift_start and shift_end <= shift_start:
            shift_end += timedelta(days=1)
        return shift_end

    def _vehicle_weight_capacity(self, driver, vehicle: Vehicle | None) -> float | None:
        if vehicle and vehicle.capacity_weight_kg is not None:
            return float(vehicle.capacity_weight_kg)
        return float(driver.max_weight_kg) if driver.max_weight_kg is not None else None

    def _vehicle_volume_capacity(self, driver, vehicle: Vehicle | None) -> float | None:
        if vehicle and vehicle.capacity_volume_m3 is not None:
            return float(vehicle.capacity_volume_m3)
        return float(driver.max_volume_m3) if driver.max_volume_m3 is not None else None

    def _capacity_text(self, remaining_weight: float | None, remaining_volume: float | None) -> str:
        weight = "unknown weight" if remaining_weight is None else f"{round(max(remaining_weight, 0), 1)} kg"
        volume = "unknown volume" if remaining_volume is None else f"{round(max(remaining_volume, 0), 2)} m3"
        return f"{weight} / {volume}"

    def _sort_orders_for_strategy(self, orders: list, strategy: str) -> list:
        if strategy == "fastest":
            return sorted(orders, key=lambda item: (item.time_window_end is None, item.time_window_end, -item.priority, item.created_at))
        if strategy == "shortest":
            return sorted(orders, key=lambda item: self._dropoff_key(item))
        return sorted(orders, key=lambda item: (-item.priority, item.time_window_start is None, item.time_window_start, item.created_at))

    def _sort_drivers_for_strategy(self, drivers: list, strategy: str) -> list:
        if strategy == "fastest":
            return sorted(drivers, key=lambda item: (item.shift_start is None, item.shift_start, item.display_name))
        if strategy == "shortest":
            return sorted(
                drivers,
                key=lambda item: (
                    float(item.current_latitude or item.home_latitude or Decimal("0")),
                    float(item.current_longitude or item.home_longitude or Decimal("0")),
                    item.display_name,
                ),
            )
        if strategy == "balanced":
            return sorted(
                drivers,
                key=lambda item: (
                    -(float(item.max_weight_kg) if item.max_weight_kg is not None else 0),
                    -(float(item.max_volume_m3) if item.max_volume_m3 is not None else 0),
                    item.shift_end is None,
                    item.shift_end,
                    item.display_name,
                ),
            )
        return sorted(drivers, key=lambda item: item.display_name)

    def _dropoff_key(self, order) -> tuple:
        dropoff = next((stop for stop in order.stops if stop.kind.value == "dropoff"), None)
        return (
            float(dropoff.latitude) if dropoff and dropoff.latitude is not None else 0,
            float(dropoff.longitude) if dropoff and dropoff.longitude is not None else 0,
            -order.priority,
        )
