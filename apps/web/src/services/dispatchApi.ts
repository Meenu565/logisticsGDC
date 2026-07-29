import type { ChatCard, ChatMessage, Coordinate, DashboardState, Driver, Order, Recommendation, Route } from "../types/dispatch";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined;
const SESSION_KEY = "smart-dispatcher-session-id";

type ApiPayload<T> = {
  success: boolean;
  message?: string;
  data: T;
};

type RawRecord = Record<string, unknown>;

function errorMessage<T>(payload: ApiPayload<T>): string {
  const data = recordValue(payload.data);
  const detail = stringValue(data?.error) ?? stringValue(data?.message);
  if (payload.message && payload.message !== "Conversation failed.") return payload.message;
  return detail ?? payload.message ?? "API request failed";
}

function headers(extra?: HeadersInit): HeadersInit {
  return {
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    ...extra,
  };
}

async function api<T>(path: string, init?: RequestInit): Promise<ApiPayload<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: headers(init?.headers),
  });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  const payload = (await response.json()) as ApiPayload<T>;
  if (payload.success === false) throw new Error(errorMessage(payload));
  return payload;
}

export async function getSessionId(): Promise<string> {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const payload = await api<{ session: { id: string } }>("/sessions?title=Today%27s%20Dispatch", {
    method: "POST",
  });
  const id = payload.data.session.id;
  localStorage.setItem(SESSION_KEY, id);
  return id;
}

export async function fetchDashboardState(): Promise<DashboardState> {
  const sessionId = await getSessionId();
  const payload = await api<RawRecord>(`/dashboard/${sessionId}`);
  return normalizeDashboard(payload.data, sessionId);
}

export async function sendChatMessage(message: string): Promise<ChatMessage> {
  const sessionId = await getSessionId();
  const payload = await api<{ intent?: string; selected_tools?: unknown[]; tool_results?: unknown[] }>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content: payload.message ?? "",
    timestamp: "now",
    cards: cardsFromChatResponse(payload.message ?? "", payload.data),
  };
}

export async function resetWorkspace(): Promise<DashboardState> {
  const sessionId = await getSessionId();
  const payload = await api<{ dashboard: RawRecord }>(`/sessions/${sessionId}/reset`, {
    method: "POST",
  });
  return normalizeDashboard(payload.data.dashboard, sessionId);
}

export async function importOrders(file: File, mode: "append" | "replace" = "append"): Promise<ChatMessage> {
  const sessionId = await getSessionId();
  const form = new FormData();
  form.append("file", file);
  const payload = await api<{ imported_rows: number; file_name: string; mode?: string; replaced_rows?: number }>(
    `/orders/import?session_id=${sessionId}&mode=${mode}`,
    {
      method: "POST",
      body: form,
    },
  );
  const replaced = payload.data.replaced_rows ? ` Replaced ${payload.data.replaced_rows} existing active orders.` : "";
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content: `Import complete. I ${mode === "replace" ? "replaced today's order set and imported" : "imported"} ${payload.data.imported_rows} orders from ${payload.data.file_name}.${replaced}`,
    timestamp: "now",
    cards: [
      {
        type: "import_success",
        title: `${payload.data.imported_rows} orders imported`,
        description: payload.data.file_name,
      },
    ],
  };
}

export async function acceptRecommendation(recommendationId: string): Promise<Recommendation> {
  const sessionId = await getSessionId();
  const payload = await api<{ recommendation: RawRecord }>(
    `/recommendations/${recommendationId}/accept?session_id=${sessionId}`,
    { method: "POST" },
  );
  return normalizeRecommendation(payload.data.recommendation);
}

export async function applyRecommendation(recommendationId: string): Promise<DashboardState> {
  const sessionId = await getSessionId();
  const payload = await api<{ dashboard: RawRecord }>(
    `/recommendations/${recommendationId}/apply?session_id=${sessionId}`,
    { method: "POST" },
  );
  return normalizeDashboard(payload.data.dashboard, sessionId);
}

export async function rejectRecommendation(recommendationId: string): Promise<Recommendation> {
  const payload = await api<{ recommendation: RawRecord }>(
    `/recommendations/${recommendationId}/reject?reason=${encodeURIComponent("Dispatcher rejected from frontend")}`,
    { method: "POST" },
  );
  return normalizeRecommendation(payload.data.recommendation);
}

export async function undoLastChange(): Promise<DashboardState> {
  const sessionId = await getSessionId();
  const payload = await api<{ dashboard: RawRecord }>(`/recommendations/session/${sessionId}/undo`, {
    method: "POST",
  });
  return normalizeDashboard(payload.data.dashboard, sessionId);
}

function normalizeDashboard(data: RawRecord, sessionId: string): DashboardState {

  const routes = normalizeRoutes(data);

  const drivers = arrayValue(data.drivers).map(raw => {
    const driver = normalizeDriver(raw);

    const route = routes.find(
      r => r.driverId === driver.id
    );

    return {
      ...driver,
      vehicle: route?.vehicle ?? driver.vehicle,
    };
  });

  return {
    sessionId: stringValue(data.session_id) ?? sessionId,
    drivers,
    orders: arrayValue(data.orders).map(normalizeOrder),
    routes,
    recommendations: arrayValue(data.recommendations).map(normalizeRecommendation),
    messages: [],
    timeline: arrayValue(data.timeline),
  };
}
function normalizeDriver(raw: RawRecord): Driver {
  return {
    id: stringValue(raw.id) ?? crypto.randomUUID(),
    name: stringValue(raw.display_name) ?? stringValue(raw.name) ?? "Driver",
    status: normalizeDriverStatus(stringValue(raw.status)),
    vehicle: stringValue(raw.vehicle) ?? stringValue(raw.vehicle_label) ?? "Unassigned",
    qualification: arrayValue(raw.qualification).map((item) => String(item)),
    capacity: capacityLabel(raw),
    location: coordinateFrom(raw.current_latitude, raw.current_longitude) ?? coordinateFrom(raw.latitude, raw.longitude),
    shiftEndsAt: formatTime(stringValue(raw.shift_end)) ?? "Not set",
  };
}

function normalizeOrder(raw: RawRecord): Order {
  const label = stringValue(raw.external_order_id) ? `Order #${raw.external_order_id}` : `Order ${stringValue(raw.id) ?? ""}`.trim();
  const stops = arrayValue(raw.stops);
  const pickup = stops.find((stop) => stringValue(stop.kind)?.toLowerCase() === "pickup");
  const dropoff = stops.find((stop) => stringValue(stop.kind)?.toLowerCase() === "dropoff");
  return {
    id: stringValue(raw.id) ?? crypto.randomUUID(),
    label,
    customer: stringValue(raw.customer_name) ?? stringValue(raw.customer) ?? "Unknown customer",
    type: normalizeDeliveryType(stringValue(raw.delivery_type) ?? stringValue(raw.delivery_type_code)),
    priority: normalizePriority(raw.priority),
    pickup: pickup ? coordinateFrom(pickup.latitude, pickup.longitude) : null,
    dropoff: dropoff ? coordinateFrom(dropoff.latitude, dropoff.longitude) : null,
    window: timeWindow(raw),
    status: normalizeOrderStatus(stringValue(raw.status)),
  };
}

function normalizeRecommendation(raw: RawRecord): Recommendation {
  const operationalBenefits = arrayValue(raw.operational_benefits).map(String);
  const metrics = parseLabeledValues(operationalBenefits, [
    "Estimated distance",
    "Estimated travel time",
    "Estimated fuel savings",
    "Vehicles used",
    "Orders covered",
  ]);
  const strategy = labeledValue(operationalBenefits, "Strategy");
  return {
    id: stringValue(raw.id) ?? crypto.randomUUID(),
    title: stringValue(raw.title) ?? "Recommendation",
    summary: stringValue(raw.reason) ?? stringValue(raw.summary) ?? "",
    strategy: strategy ?? undefined,
    benefits: prefixedValues(operationalBenefits, "Pros"),
    risks: prefixedValues(operationalBenefits, "Cons"),
    metrics,
    whyRecommended: labeledValue(operationalBenefits, "AI recommendation") ?? undefined,
    fromDriver: stringValue(raw.from_driver_id) ?? stringValue(raw.fromDriver) ?? "Current driver",
    toDriver: stringValue(raw.to_driver_id) ?? stringValue(raw.toDriver) ?? "Proposed driver",
    timeSavedSeconds: numberValue(raw.time_saved_seconds) ?? numberValue(raw.timeSavedSeconds) ?? 0,
    distanceSavedMeters: numberValue(raw.distance_saved_meters) ?? numberValue(raw.distanceSavedMeters) ?? 0,
    status: normalizeRecommendationStatus(stringValue(raw.status)),
    routeId: stringValue(raw.proposed_plan_id) ?? stringValue(raw.routeId) ?? "",
  };
}

function normalizeRoutes(data: RawRecord): Route[] {
  const rawRoutes = arrayValue(data.routes);
  if (rawRoutes.length) {
    return rawRoutes.map((raw, index) => normalizeRoute(raw, index));
  }
  const currentPlan = recordValue(data.current_plan);
  if (!currentPlan) return [];
  const distanceMeters = numberValue(currentPlan.distance_meters) ?? 0;
  const travelSeconds = numberValue(currentPlan.travel_seconds) ?? 0;
  if (!distanceMeters && !travelSeconds) return [];
  return [
    {
      id: stringValue(currentPlan.plan_id) ?? "current-plan",
      driverId: "",
      color: "#3b82f6",
      distanceMeters,
      travelSeconds,
      coordinates: [],
      stopLabels: ["Current plan"],
    },
  ];
}

function normalizeRoute(raw: RawRecord, index: number): Route {
  const coordinates = arrayValue(raw.coordinates)
    .map((item) => {
      const point = recordValue(item);
      if (!point) return null;

      return {
        latitude: numberValue(point.latitude)!,
        longitude: numberValue(point.longitude)!,
      };
    })
    .filter(
      (point): point is Coordinate =>
        point !== null &&
        Number.isFinite(point.latitude) &&
        Number.isFinite(point.longitude),
    );

  const stopLabels =
    arrayValue(raw.stopLabels).map(String).length > 0
      ? arrayValue(raw.stopLabels).map(String)
      : arrayValue(raw.stop_labels).map(String);

  const stops = arrayValue(raw.stops).map((item) => {
    const stop = recordValue(item);
    const latitude = numberValue(stop?.latitude);
    const longitude = numberValue(stop?.longitude);

    return {
      sequence: numberValue(stop?.sequence) ?? 0,
      label: stringValue(stop?.label) ?? "",
      orderId: stringValue(stop?.orderId) ?? stringValue(stop?.order_id) ?? undefined,
      orderLabel: stringValue(stop?.orderLabel) ?? stringValue(stop?.order_label) ?? undefined,
      coordinate:
        latitude !== null && longitude !== null
          ? { latitude, longitude }
          : null,
      arrival: stringValue(stop?.arrival),
      departure: stringValue(stop?.departure),
      serviceMinutes: numberValue(stop?.serviceMinutes),
      travelSecondsFromPrevious: numberValue(stop?.travelSecondsFromPrevious),
      distanceMetersFromPrevious: numberValue(stop?.distanceMetersFromPrevious),
    };
  });

  return {
    id: stringValue(raw.id) ?? crypto.randomUUID(),

    driverId:
      stringValue(raw.driverId) ??
      stringValue(raw.driver_id) ??
      "",

    vehicle:
      stringValue(raw.vehicle) ??
      "Unassigned",

    vehicleId:
      stringValue(raw.vehicleId) ??
      stringValue(raw.vehicle_id) ??
      "",

    routeDate:
      stringValue(raw.routeDate) ??
      stringValue(raw.route_date) ??
      "",
    startsAt:
      stringValue(raw.startsAt) ??
      stringValue(raw.starts_at),

    endsAt:
      stringValue(raw.endsAt) ??
      stringValue(raw.ends_at),

    color:
      stringValue(raw.color) ??
      ["#3b82f6", "#22c55e", "#f97316", "#a855f7"][index % 4],

    distanceMeters:
      numberValue(raw.distanceMeters) ??
      numberValue(raw.distance_meters) ??
      0,

    travelSeconds:
      numberValue(raw.travelSeconds) ??
      numberValue(raw.travel_seconds) ??
      0,

    coordinates,

    stopLabels,

    stops,
  };
}


function cardsFromChatResponse(message: string, data: { selected_tools?: unknown[]; tool_results?: unknown[] }): ChatCard[] {
  const toolResults = arrayValue(data.tool_results);
  const recommendations = dedupeRecommendations(toolResults.flatMap((item) => {
    const result = recordValue(item.result);
    const resultData = recordValue(result?.data);
    const generated = recordValue(resultData?.recommendation);
    const generatedMany = arrayValue(resultData?.recommendations);
    if (generated) return [normalizeRecommendation(generated)];
    return generatedMany.map(normalizeRecommendation);
  }));
  if (recommendations.length) {
    return recommendations.map((recommendation) => ({
      type: "recommendation",
      title: recommendation.title,
      description: recommendation.summary || message,
      payload: { recommendation },
    }));
  }
  const toolNames = arrayValue(data.selected_tools)
    .map((item) => stringValue(item.tool_name))
    .filter(Boolean);
  if (toolNames.some((name) => name?.includes("eta"))) {
    return [{ type: "eta", title: "ETA", description: message }];
  }
  if (toolNames.some((name) => name?.includes("route") || name?.includes("plan"))) {
    return [{ type: "route_summary", title: "Route update", description: message }];
  }
  return [];
}

function coordinateFrom(latitude: unknown, longitude: unknown): Coordinate | null {
  const lat = numberValue(latitude);
  const lng = numberValue(longitude);
  if (lat == null || lng == null) return null;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return { latitude: lat, longitude: lng };
}

function arrayValue(value: unknown): RawRecord[] {
  return Array.isArray(value) ? (value as RawRecord[]) : [];
}

function recordValue(value: unknown): RawRecord | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as RawRecord) : null;
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function prefixedValues(values: string[], prefix: string): string[] {
  return values
    .filter((value) => value.startsWith(`${prefix}:`))
    .map((value) => value.slice(prefix.length + 1).trim())
    .filter(Boolean);
}

function labeledValue(values: string[], label: string): string | null {
  const match = values.find((value) => value.startsWith(`${label}:`));
  return match ? match.slice(label.length + 1).trim() : null;
}

function parseLabeledValues(values: string[], labels: string[]): Record<string, string> {
  return labels.reduce<Record<string, string>>((metrics, label) => {
    const value = labeledValue(values, label);
    if (value) metrics[label] = value;
    return metrics;
  }, {});
}

function dedupeRecommendations(recommendations: Recommendation[]): Recommendation[] {
  const seen = new Set<string>();
  return recommendations.filter((recommendation) => {
    if (seen.has(recommendation.id)) return false;
    seen.add(recommendation.id);
    return true;
  });
}

function normalizeDriverStatus(value: string | null): Driver["status"] {
  if (value === "assigned" || value === "on_route" || value === "delayed" || value === "unavailable") return value;
  return "available";
}

function normalizeOrderStatus(value: string | null): Order["status"] {
  if (value === "planned" || value === "assigned" || value === "cancelled") return value;
  return "new";
}

function normalizeRecommendationStatus(value: string | null): Recommendation["status"] {
  if (value === "accepted" || value === "rejected" || value === "applied" || value === "undone") return value;
  return "proposed";
}

function normalizePriority(value: unknown): Order["priority"] {
  const priority = numberValue(value) ?? 0;
  if (priority >= 8) return "urgent";
  if (priority >= 4) return "high";
  return "normal";
}

function normalizeDeliveryType(value: string | null): Order["type"] {
  const normalized = value?.toLowerCase();
  if (normalized?.includes("white")) return "White Glove";
  if (normalized?.includes("threshold")) return "Threshold";
  return "Curbside";
}

function capacityLabel(raw: RawRecord) {
  const weight = numberValue(raw.max_weight_kg);
  const volume = numberValue(raw.max_volume_m3);
  if (weight && volume) return `${weight} kg / ${volume} m3`;
  if (weight) return `${weight} kg`;
  if (volume) return `${volume} m3`;
  return "Not set";
}

function formatTime(value: string | null) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function timeWindow(raw: RawRecord) {
  const start = formatTime(stringValue(raw.time_window_start));
  const end = formatTime(stringValue(raw.time_window_end));
  if (start && end) return `${start} - ${end}`;
  if (start) return `After ${start}`;
  if (end) return `Before ${end}`;
  return "Not set";
}
