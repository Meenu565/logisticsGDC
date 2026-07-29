export type Coordinate = {
  latitude: number;
  longitude: number;
};

export type Driver = {
  id: string;
  name: string;
  status: "available" | "assigned" | "on_route" | "delayed" | "unavailable";
  vehicle: string;
  qualification: string[];
  capacity: string;
  location: Coordinate | null;
  shiftEndsAt: string;
};

export type Order = {
  id: string;
  label: string;
  customer: string;
  type: "Curbside" | "Threshold" | "White Glove";
  priority: "normal" | "high" | "urgent";
  pickup: Coordinate | null;
  dropoff: Coordinate | null;
  window: string;
  status: "new" | "planned" | "assigned" | "cancelled";
};

export type RouteStop = {
  sequence: number;
  label: string;
  orderId?: string;
  orderLabel?: string;
  coordinate?: Coordinate | null;
  arrival?: string | null;
  departure?: string | null;
  serviceMinutes?: number | null;
  travelSecondsFromPrevious?: number | null;
  distanceMetersFromPrevious?: number | null;
};

export type Route = {
  id: string;
  driverId: string;

  vehicle?: string;
  vehicleId?: string;
  routeDate?: string;
  startsAt?: string | null;
  endsAt?: string | null;

  color: string;
  distanceMeters: number;
  travelSeconds: number;

  coordinates: Coordinate[];

  stopLabels: string[];

  stops?: RouteStop[];
};
export type Recommendation = {
  id: string;
  title: string;
  summary: string;
  strategy?: string;
  benefits?: string[];
  risks?: string[];
  metrics?: Record<string, string>;
  whyRecommended?: string;
  fromDriver: string;
  toDriver: string;
  timeSavedSeconds: number;
  distanceSavedMeters: number;
  status: "proposed" | "accepted" | "rejected" | "applied" | "undone";
  routeId: string;
};

export type ChatCardType =
  | "route_summary"
  | "driver_assignment"
  | "optimization_complete"
  | "recommendation"
  | "eta"
  | "import_success"
  | "driver_info"
  | "order_info";

export type ChatCard = {
  type: ChatCardType;
  title: string;
  description: string;
  payload?: Record<string, unknown>;
};

export type ChatMessage = {
  id: string;
  role: "assistant" | "dispatcher";
  content: string;
  timestamp: string;
  cards?: ChatCard[];
};

export type ContextPanel =
  | { kind: "driver"; driver: Driver }
  | { kind: "order"; order: Order }
  | { kind: "route"; route: Route }
  | { kind: "recommendation"; recommendation: Recommendation }
  | { kind: "eta"; title: string; items: string[] };

export type DashboardState = {
  sessionId?: string;
  drivers: Driver[];
  orders: Order[];
  routes: Route[];
  recommendations: Recommendation[];
  messages: ChatMessage[];
  timeline?: unknown[];
};
