from app.optimization.types import (
    OptimizationResult,
    PlannedRoute,
    PlannedRouteStop,
    PlanningDriver,
    PlanningStop,
)
from app.providers.types import Coordinate, RouteMatrix


class RouteOptimizer:
    #Checks Inputs: Returns empty results immediately if drivers or stops are missing.
    # Dual-Strategy: Tries the smart Google engine first, falling back to a simpler method if it fails.
    def optimize(
        self,
        drivers: list[PlanningDriver],
        stops: list[PlanningStop],
        matrix: RouteMatrix,
    ) -> OptimizationResult:
        if not drivers or not stops:
            return OptimizationResult(
                routes=[],
                total_distance_meters=0,
                total_travel_seconds=0,
                total_dwell_seconds=0,
                unassigned_stop_ids=[stop.stop_id for stop in stops],
                engine="none",
            )

        try:
            return self._optimize_with_ortools(drivers, stops, matrix)
        except ImportError:
            return self._optimize_greedy(drivers, stops, matrix)
#2. Primary Method 
# (_optimize_with_ortools)Uses Google OR-Tools: Employs an advanced mathematical solver.
# Minimizes Time: Calculates paths to find the absolute cheapest travel times.
# Fallback Trigger: Reverts to the backup method if no solution is found.
    def _optimize_with_ortools(
        self,
        drivers: list[PlanningDriver],
        stops: list[PlanningStop],
        matrix: RouteMatrix,
    ) -> OptimizationResult:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2

        starts = list(range(len(drivers)))
        manager = pywrapcp.RoutingIndexManager(len(stops) + len(drivers), len(drivers), starts, starts)
        routing = pywrapcp.RoutingModel(manager)
#3. Backup Method 
# (_optimize_greedy)Prioritizes Stops: Sorts deliveries by importance and ID.
# Round-Robin Sharing: Splits stops evenly among drivers one by one.
# Simplistic Logic: Fast but less optimized than Google's engine.
        def transit_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return matrix.durations_seconds[from_node][to_node]

        transit_index = routing.RegisterTransitCallback(transit_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_index)

        

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        solution = routing.SolveWithParameters(search_parameters)
        if solution is None:
            return self._optimize_greedy(drivers, stops, matrix)

        return self._read_solution(drivers, stops, matrix, manager, routing, solution, engine="ortools")

#Data Packaging (_read_solution)Tracks Metrics: Totals up meters driven, travel seconds, and parking wait times.
# Catches Misses: Identifies and lists any leftover unassigned stops.
    def _read_solution(
        self,
        drivers: list[PlanningDriver],
        stops: list[PlanningStop],
        matrix: RouteMatrix,
        manager,
        routing,
        solution,
        engine: str,
    ) -> OptimizationResult:
        planned_routes: list[PlannedRoute] = []
        for vehicle_index, driver in enumerate(drivers):
            index = routing.Start(vehicle_index)
            route_stops: list[PlannedRouteStop] = []
            distance_meters = 0
            travel_seconds = 0
            dwell_seconds = 0
            previous_node = manager.IndexToNode(index)

            while not routing.IsEnd(index):
                next_index = solution.Value(routing.NextVar(index))
                node = manager.IndexToNode(next_index)
                if node >= len(drivers):
                    stop = stops[node - len(drivers)]
                    leg_distance = matrix.distances_meters[previous_node][node]
                    leg_seconds = matrix.durations_seconds[previous_node][node]
                    distance_meters += leg_distance
                    travel_seconds += leg_seconds
                    dwell_seconds += stop.dwell_seconds
                    route_stops.append(
                        PlannedRouteStop(
                            stop_id=stop.stop_id,
                            order_id=stop.order_id,
                            sequence_number=len(route_stops) + 1,
                            travel_seconds_from_previous=leg_seconds,
                            distance_meters_from_previous=leg_distance,
                            dwell_seconds=stop.dwell_seconds,
                        )
                    )
                previous_node = node
                index = next_index

            if route_stops:
                planned_routes.append(
                    PlannedRoute(
                        driver_id=driver.driver_id,
                        vehicle_id=driver.vehicle_id,
                        stops=route_stops,
                        distance_meters=distance_meters,
                        travel_seconds=travel_seconds,
                        dwell_seconds=dwell_seconds,
                    )
                )

        assigned = {route_stop.stop_id for route in planned_routes for route_stop in route.stops}
        return OptimizationResult(
            routes=planned_routes,
            total_distance_meters=sum(route.distance_meters for route in planned_routes),
            total_travel_seconds=sum(route.travel_seconds for route in planned_routes),
            total_dwell_seconds=sum(route.dwell_seconds for route in planned_routes),
            unassigned_stop_ids=[stop.stop_id for stop in stops if stop.stop_id not in assigned],
            engine=engine,
        )

    def _optimize_greedy(
        self,
        drivers: list[PlanningDriver],
        stops: list[PlanningStop],
        matrix: RouteMatrix,
    ) -> OptimizationResult:
        route_buckets: list[list[PlanningStop]] = [[] for _ in drivers]
        for index, stop in enumerate(sorted(stops, key=lambda item: (-item.priority, item.stop_id.hex))):
            route_buckets[index % len(drivers)].append(stop)

        planned_routes: list[PlannedRoute] = []
        for driver_index, driver in enumerate(drivers):
            route_stops: list[PlannedRouteStop] = []
            previous_node = driver_index
            distance_meters = 0
            travel_seconds = 0
            dwell_seconds = 0
            for stop in route_buckets[driver_index]:
                node = len(drivers) + stops.index(stop)
                leg_distance = matrix.distances_meters[previous_node][node]
                leg_seconds = matrix.durations_seconds[previous_node][node]
                distance_meters += leg_distance
                travel_seconds += leg_seconds
                dwell_seconds += stop.dwell_seconds
                route_stops.append(
                    PlannedRouteStop(
                        stop_id=stop.stop_id,
                        order_id=stop.order_id,
                        sequence_number=len(route_stops) + 1,
                        travel_seconds_from_previous=leg_seconds,
                        distance_meters_from_previous=leg_distance,
                        dwell_seconds=stop.dwell_seconds,
                    )
                )
                previous_node = node
            if route_stops:
                planned_routes.append(
                    PlannedRoute(
                        driver_id=driver.driver_id,
                        vehicle_id=driver.vehicle_id,
                        stops=route_stops,
                        distance_meters=distance_meters,
                        travel_seconds=travel_seconds,
                        dwell_seconds=dwell_seconds,
                    )
                )

        return OptimizationResult(
            routes=planned_routes,
            total_distance_meters=sum(route.distance_meters for route in planned_routes),
            total_travel_seconds=sum(route.travel_seconds for route in planned_routes),
            total_dwell_seconds=sum(route.dwell_seconds for route in planned_routes),
            engine="greedy_fallback",
        )


def coordinates_for_problem(drivers: list[PlanningDriver], stops: list[PlanningStop]) -> list[Coordinate]:
    return [
        *[
            Coordinate(latitude=driver.start_latitude, longitude=driver.start_longitude)
            for driver in drivers
        ],
        *[Coordinate(latitude=stop.latitude, longitude=stop.longitude) for stop in stops],
    ]
