from uuid import UUID

from sqlalchemy import select

from app.models import DispatchPlan, Vehicle
from app.repositories.routes import DispatchPlanRepository, RouteRepository


class RouteService:
    def __init__(
        self,
        plans: DispatchPlanRepository,
        routes: RouteRepository,
    ) -> None:
        self.plans = plans
        self.routes = routes

    def current_plan(self, session_id: UUID) -> DispatchPlan | None:
        return self.plans.current_for_session(session_id)

    def route_summary(self, plan_id: UUID) -> dict:
        routes = list(self.routes.list_for_plan(plan_id))

        return {
            "plan_id": str(plan_id),
            "route_count": len(routes),
            "distance_meters": sum(route.distance_meters for route in routes),
            "travel_seconds": sum(route.travel_seconds for route in routes),
            "dwell_seconds": sum(route.dwell_seconds for route in routes),
        }

    def list_routes(self, plan_id: UUID) -> list[dict]:
        routes = self.routes.list_for_plan(plan_id)

        colors = [
            "#3B82F6",
            "#22C55E",
            "#F97316",
            "#EC4899",
            "#A855F7",
            "#EAB308",
        ]

        vehicles = {
            str(vehicle.id): vehicle.label
            for vehicle in self.routes.db.scalars(select(Vehicle)).all()
        }

        result = []

        for index, route in enumerate(routes):
            coordinates = []
            stop_labels = []
            stop_details = []

            for route_stop in self.routes.list_route_stops(route.id):
                stop = self.routes.get_stop(route_stop.stop_id)

                if not stop:
                    continue

                # Coordinates for map
                if stop.latitude is not None and stop.longitude is not None:
                    coordinates.append(
                        {
                            "latitude": float(stop.latitude),
                            "longitude": float(stop.longitude),
                        }
                    )

                # Existing stop labels
                stop_labels.append(stop.address_line1)

                # NEW: Detailed stop information for ETA panel
                stop_details.append(
                    {
                        "orderId": str(stop.order_id),
                        "orderLabel": stop.order.external_order_id or stop.order.customer_name,
                        "label": stop.address_line1,
                        "latitude": float(stop.latitude) if stop.latitude is not None else None,
                        "longitude": float(stop.longitude) if stop.longitude is not None else None,
                        "arrival": (
                            route_stop.planned_arrival_at.isoformat()
                            if route_stop.planned_arrival_at
                            else None
                        ),
                        "departure": (
                            route_stop.planned_departure_at.isoformat()
                            if route_stop.planned_departure_at
                            else None
                        ),
                        "serviceMinutes": stop.service_minutes,
                        "sequence": route_stop.sequence_number,
                        "travelSecondsFromPrevious": route_stop.travel_seconds_from_previous,
                        "distanceMetersFromPrevious": route_stop.distance_meters_from_previous,
                    }
                )

            result.append(
                {
                    "id": str(route.id),
                    "driverId": str(route.driver_id) if route.driver_id else None,
                    "vehicle": vehicles.get(
                        str(route.vehicle_id),
                        "Unassigned",
                    ),
                    "vehicleId": (
                        str(route.vehicle_id)
                        if route.vehicle_id
                        else None
                    ),
                    "routeDate": (
                        route.route_date.isoformat()
                        if route.route_date
                        else None
                    ),
                    "startsAt": route.starts_at.isoformat() if route.starts_at else None,
                    "endsAt": route.ends_at.isoformat() if route.ends_at else None,
                    "color": colors[index % len(colors)],
                    "distanceMeters": route.distance_meters,
                    "travelSeconds": route.travel_seconds,
                    "coordinates": coordinates,
                    "stopLabels": stop_labels,

                    # NEW
                    "stops": stop_details,
                }
            )

        return result
