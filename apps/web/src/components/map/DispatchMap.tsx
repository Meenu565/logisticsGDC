import { useEffect, useMemo, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import type { Feature, FeatureCollection, LineString } from "geojson";
import { Navigation } from "lucide-react";
import type { Coordinate, DashboardState, Order, Route } from "../../types/dispatch";
import { cn, formatDistance, formatMinutes } from "../../lib/utils";
import { useDispatchStore } from "../../store/useDispatchStore";
import { getRoadGeometry } from "../../lib/mapboxDirections";

type DispatchMapProps = {
  dashboard: DashboardState;
};

type StopMarkerPoint = {
  coordinate: Coordinate;
  label: string;
};

const ROUTES_SOURCE = "dispatch-routes";
const SELECTED_ROUTE_SOURCE = "selected-dispatch-route";
const ROUTES_LAYER = "dispatch-routes-layer";
const SELECTED_ROUTE_LAYER = "selected-dispatch-route-layer";

export function DispatchMap({ dashboard }: DispatchMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker[]>([]);
  const token = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;
  const [roadRoutes, setRoadRoutes] = useState<Route[]>([]);

  const selectedRouteId = useDispatchStore((state) => state.selectedRouteId);
  const selectedDriverId = useDispatchStore((state) => state.selectedDriverId);
  const selectedOrderId = useDispatchStore((state) => state.selectedOrderId);
  const selectedRecommendationId = useDispatchStore((state) => state.selectedRecommendationId);
  const selectDriver = useDispatchStore((state) => state.selectDriver);
  const selectOrder = useDispatchStore((state) => state.selectOrder);
  const selectRoute = useDispatchStore((state) => state.selectRoute);

  const selectedRoute = useMemo(
    () => dashboard.routes.find((route) => route.id === selectedRouteId) ?? dashboard.routes[0],
    [dashboard.routes, selectedRouteId],
  );
  const selectedOrder = dashboard.orders.find((order) => order.id === selectedOrderId);
  const selectedDriver = dashboard.drivers.find((driver) => driver.id === selectedDriverId);
  const selectedRecommendation = dashboard.recommendations.find((item) => item.id === selectedRecommendationId);

  useEffect(() => {
    if (!containerRef.current || !token || mapRef.current) return;
    mapboxgl.accessToken = token;
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-79.395, 43.66],
      zoom: 11.8,
      pitch: 36,
      bearing: -8,
      attributionControl: false,
    });
    mapRef.current.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "bottom-right");
    return () => {
      markerRef.current.forEach((marker) => marker.remove());
      markerRef.current = [];
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [token]);

  useEffect(() => {
    let cancelled = false;

    async function buildRoadRoutes() {
      const updated = await Promise.all(
        dashboard.routes.map(async (route) => ({
          ...route,
          coordinates: await getRoadGeometry(route.coordinates),
        })),
      );
      if (!cancelled) setRoadRoutes(updated);
    }

    if (dashboard.routes.length && token) buildRoadRoutes();
    else setRoadRoutes([]);

    return () => {
      cancelled = true;
    };
  }, [dashboard.routes, token]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const paintRoutes = () => {
      const routesToDraw = roadRoutes.length > 0 ? roadRoutes : dashboard.routes;
      const selectedRoadRoute = routesToDraw.find((route) => route.id === selectedRoute?.id);
      const routesData = routeCollection(routesToDraw);
      const selectedData = routeCollection(selectedRoadRoute ? [selectedRoadRoute] : []);

      if (map.getSource(ROUTES_SOURCE)) {
        (map.getSource(ROUTES_SOURCE) as mapboxgl.GeoJSONSource).setData(routesData);
      } else {
        map.addSource(ROUTES_SOURCE, { type: "geojson", data: routesData });
        map.addLayer({
          id: ROUTES_LAYER,
          type: "line",
          source: ROUTES_SOURCE,
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["coalesce", ["get", "color"], "#3b82f6"],
            "line-width": 4,
            "line-opacity": 0.42,
            "line-blur": 0.4,
          },
        });
      }

      if (map.getSource(SELECTED_ROUTE_SOURCE)) {
        (map.getSource(SELECTED_ROUTE_SOURCE) as mapboxgl.GeoJSONSource).setData(selectedData);
      } else {
        map.addSource(SELECTED_ROUTE_SOURCE, { type: "geojson", data: selectedData });
        map.addLayer({
          id: SELECTED_ROUTE_LAYER,
          type: "line",
          source: SELECTED_ROUTE_SOURCE,
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": ["coalesce", ["get", "color"], "#3b82f6"],
            "line-width": 6,
            "line-opacity": 0.92,
            "line-blur": 0.2,
          },
        });
      }
    };

    if (map.loaded()) paintRoutes();
    else map.once("load", paintRoutes);
  }, [dashboard.routes, roadRoutes, selectedRoute]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    markerRef.current.forEach((marker) => marker.remove());
    markerRef.current = [];

    dashboard.drivers.forEach((driver) => {
      if (!driver.location) return;
      const route = dashboard.routes.find((item) => item.driverId === driver.id);
      markerRef.current.push(
        createMarker({
          map,
          coordinate: driver.location,
          label: driver.name,
          detail: driver.vehicle,
          kind: "driver",
          active: driver.id === selectedDriverId || route?.id === selectedRoute?.id,
          onClick: () => selectDriver(driver, route),
        }),
      );
    });

    dashboard.routes.forEach((route) => {
      const stops = stopCoordinates(route);
      stops.forEach((stop, index) => {
        markerRef.current.push(
          createStopMarker({
            map,
            coordinate: stop.coordinate,
            number: index + 1,
            label: stop.label,
            kind: index === 0 ? "start" : index === stops.length - 1 ? "end" : "stop",
            active: route.id === selectedRoute?.id,
          }),
        );
      });
    });

    dashboard.orders.forEach((order) => {
      const route = routeForOrder(order, dashboard.routes);
      if (route) return;
      if (order.pickup) {
        markerRef.current.push(
          createMarker({
            map,
            coordinate: order.pickup,
            label: order.label.replace("Order #", "#"),
            kind: "pickup",
            active: order.id === selectedOrderId,
            onClick: () => selectOrder(order, route),
          }),
        );
      }
      if (order.dropoff) {
        markerRef.current.push(
          createMarker({
            map,
            coordinate: order.dropoff,
            label: order.label.replace("Order #", "#"),
            kind: "dropoff",
            active: order.id === selectedOrderId,
            onClick: () => selectOrder(order, route),
          }),
        );
      }
    });
  }, [dashboard, selectDriver, selectOrder, selectedDriverId, selectedOrderId, selectedRoute?.id]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const coordinates = focusCoordinates(selectedRoute, selectedDriver?.location, selectedOrder);
    if (!coordinates.length) return;
    const bounds = new mapboxgl.LngLatBounds();
    coordinates.forEach((point) => bounds.extend([point.longitude, point.latitude]));
    map.fitBounds(bounds, {
      padding: { top: 120, bottom: 120, left: 120, right: 120 },
      duration: 900,
      maxZoom: selectedDriver || selectedOrder ? 13.8 : 12.8,
    });
  }, [selectedRoute, selectedDriver, selectedOrder, selectedRecommendation]);

  return (
    <section className="relative h-full overflow-hidden rounded-[24px] border border-white/10 bg-[#050913] shadow-soft">
      <div ref={containerRef} className="absolute inset-0" />
      {!token && <MapTokenState />}
      {token && !hasMapContent(dashboard) && <EmptyMapState />}
      <div className="pointer-events-none absolute left-4 top-4 rounded-full border border-white/10 bg-slate-950/82 px-3 py-1.5 text-xs text-slate-200 shadow-soft">
        Live route workspace
      </div>
      {selectedRoute && (
        <button
          type="button"
          onClick={() => selectRoute(selectedRoute)}
          className="absolute bottom-4 left-4 right-4 rounded-2xl border border-white/10 bg-slate-950/90 p-4 text-left shadow-soft transition hover:border-blue-300/35"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-white">
                {dashboard.drivers.find((driver) => driver.id === selectedRoute.driverId)?.name ?? "Selected route"}
              </div>
              <div className="mt-1 text-xs text-slate-400">{selectedRoute.stopLabels.join(" -> ")}</div>
            </div>
            <div className="shrink-0 text-right text-xs text-slate-300">
              <div>{formatMinutes(selectedRoute.travelSeconds)}</div>
              <div>{formatDistance(selectedRoute.distanceMeters)}</div>
            </div>
          </div>
        </button>
      )}
    </section>
  );
}

function routeForOrder(order: Order, routes: Route[]) {
  return routes.find((route) =>
    route.stops?.some((stop) => {
      if (stop.orderId && stop.orderId === order.id) return true;
      if (stop.orderLabel && (stop.orderLabel === order.label || order.label.includes(stop.orderLabel))) return true;
      return false;
    }),
  );
}

function createMarker({
  map,
  coordinate,
  label,
  detail,
  kind,
  active,
  onClick,
}: {
  map: mapboxgl.Map;
  coordinate: Coordinate;
  label: string;
  detail?: string;
  kind: "driver" | "pickup" | "dropoff";
  active: boolean;
  onClick: () => void;
}) {
  const element = document.createElement("button");
  element.type = "button";
  element.className = cn("dispatch-marker", `dispatch-marker-${kind}`, active && "dispatch-marker-active");
  element.setAttribute("aria-label", label);

  if (kind === "driver") {
    const wrapper = document.createElement("div");
    wrapper.className = "dispatch-driver-marker";

    const icon = document.createElement("span");
    icon.textContent = "DR";
    icon.className = "dispatch-driver-icon";

    const copy = document.createElement("span");
    copy.className = "dispatch-driver-copy";

    const name = document.createElement("span");
    name.textContent = label;
    name.className = "dispatch-driver-name";

    const vehicle = document.createElement("span");
    vehicle.textContent = detail ?? "Unassigned";
    vehicle.className = "dispatch-driver-vehicle";

    copy.appendChild(name);
    copy.appendChild(vehicle);
    wrapper.appendChild(icon);
    wrapper.appendChild(copy);
    element.appendChild(wrapper);
  } else {
    const text = document.createElement("span");
    text.textContent = label;
    element.appendChild(text);
  }

  element.addEventListener("click", onClick);

  return new mapboxgl.Marker({ element, anchor: "center" })
    .setLngLat([coordinate.longitude, coordinate.latitude])
    .addTo(map);
}

function routeCollection(routes: Route[]): FeatureCollection<LineString> {
  return {
    type: "FeatureCollection",
    features: routes.filter((route) => route.coordinates.length >= 2).map(routeFeature),
  };
}

function stopCoordinates(route: Route): StopMarkerPoint[] {
  const stops =
    route.stops
      ?.filter((stop) => stop.coordinate)
      .sort((a, b) => a.sequence - b.sequence)
      .map((stop) => ({
        coordinate: stop.coordinate!,
        label: stop.label || `Stop ${stop.sequence}`,
      })) ?? [];

  if (stops.length > 0) return stops;

  return route.coordinates.map((coordinate, index) => ({
    coordinate,
    label: `Stop ${index + 1}`,
  }));
}

function createStopMarker({
  map,
  coordinate,
  number,
  label,
  kind,
  active,
}: {
  map: mapboxgl.Map;
  coordinate: Coordinate;
  number: number;
  label: string;
  kind: "start" | "stop" | "end";
  active: boolean;
}) {
  const element = document.createElement("div");
  element.className = cn("dispatch-stop-marker", `dispatch-stop-${kind}`, active && "dispatch-stop-active");
  element.setAttribute(
    "aria-label",
    `${kind === "start" ? "Route Start" : kind === "end" ? "Route End" : "Stop"} ${number}: ${label}`,
  );

  const text = document.createElement("span");
  text.textContent = kind === "start" ? "S" : kind === "end" ? "E" : String(number);
  element.appendChild(text);

  return new mapboxgl.Marker({ element, anchor: "center" })
    .setLngLat([coordinate.longitude, coordinate.latitude])
    .addTo(map);
}

function routeFeature(route: Route): Feature<LineString> {
  return {
    type: "Feature",
    properties: { id: route.id, color: route.color },
    geometry: {
      type: "LineString",
      coordinates: route.coordinates.map((point) => [point.longitude, point.latitude]),
    },
  };
}

function focusCoordinates(route?: Route, driverLocation?: Coordinate | null, order?: Order) {
  if (order) return [order.pickup, order.dropoff].filter((point): point is Coordinate => Boolean(point));
  if (driverLocation) return [driverLocation];
  return route ? stopCoordinates(route).map((stop) => stop.coordinate) : [];
}

function hasMapContent(dashboard: DashboardState) {
  return (
    dashboard.routes.some((route) => route.coordinates.length > 0 || route.stops?.some((stop) => stop.coordinate)) ||
    dashboard.drivers.some((driver) => driver.location) ||
    dashboard.orders.some((order) => order.pickup || order.dropoff)
  );
}

function MapTokenState() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-[#050913] p-6">
      <div className="max-w-[260px] text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-200">
          <Navigation className="h-5 w-5" />
        </div>
        <div className="mt-4 text-sm font-semibold text-white">Mapbox token required</div>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Add `VITE_MAPBOX_TOKEN` to render the live dispatch map with route and marker synchronization.
        </p>
      </div>
    </div>
  );
}

function EmptyMapState() {
  return (
    <div className="pointer-events-none absolute inset-x-4 top-16 rounded-2xl border border-white/10 bg-slate-950/86 p-4 text-sm text-slate-300 shadow-soft">
      No mapped stops or driver locations yet. Import orders with latitude/longitude fields or optimize a plan to draw routes.
    </div>
  );
}
