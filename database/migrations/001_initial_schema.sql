CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE driver_status AS ENUM (
  'available',
  'assigned',
  'on_route',
  'delayed',
  'off_shift',
  'unavailable'
);

CREATE TYPE vehicle_status AS ENUM (
  'available',
  'assigned',
  'maintenance',
  'unavailable'
);

CREATE TYPE order_status AS ENUM (
  'new',
  'planned',
  'assigned',
  'in_progress',
  'completed',
  'cancelled'
);

CREATE TYPE stop_kind AS ENUM (
  'pickup',
  'dropoff'
);

CREATE TYPE route_status AS ENUM (
  'draft',
  'proposed',
  'approved',
  'active',
  'completed',
  'cancelled'
);

CREATE TYPE recommendation_status AS ENUM (
  'proposed',
  'accepted',
  'rejected',
  'applied',
  'undone',
  'expired'
);

CREATE TYPE message_role AS ENUM (
  'dispatcher',
  'assistant',
  'tool',
  'system'
);

CREATE TYPE import_status AS ENUM (
  'pending',
  'completed',
  'failed'
);

CREATE TABLE delivery_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  dwell_minutes INTEGER NOT NULL CHECK (dwell_minutes >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE drivers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name TEXT NOT NULL,
  status driver_status NOT NULL DEFAULT 'available',
  max_weight_kg NUMERIC(10, 2),
  max_volume_m3 NUMERIC(10, 2),
  shift_start TIMESTAMPTZ,
  shift_end TIMESTAMPTZ,
  home_address_line1 TEXT,
  home_address_line2 TEXT,
  home_city TEXT,
  home_region TEXT,
  home_postal_code TEXT,
  home_country TEXT NOT NULL DEFAULT 'Canada',
  home_latitude NUMERIC(9, 6),
  home_longitude NUMERIC(9, 6),
  current_latitude NUMERIC(9, 6),
  current_longitude NUMERIC(9, 6),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (shift_end IS NULL OR shift_start IS NULL OR shift_end > shift_start)
);

CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  label TEXT NOT NULL,
  status vehicle_status NOT NULL DEFAULT 'available',
  capacity_weight_kg NUMERIC(10, 2) NOT NULL CHECK (capacity_weight_kg >= 0),
  capacity_volume_m3 NUMERIC(10, 2) NOT NULL CHECK (capacity_volume_m3 >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE driver_vehicle_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
  vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  released_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (released_at IS NULL OR released_at > assigned_at)
);

CREATE UNIQUE INDEX uq_driver_vehicle_active_vehicle
  ON driver_vehicle_assignments(vehicle_id)
  WHERE released_at IS NULL;

CREATE UNIQUE INDEX uq_driver_vehicle_active_driver
  ON driver_vehicle_assignments(driver_id)
  WHERE released_at IS NULL;

CREATE TABLE driver_delivery_types (
  driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
  delivery_type_id UUID NOT NULL REFERENCES delivery_types(id) ON DELETE CASCADE,
  is_qualified BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (driver_id, delivery_type_id)
);

CREATE TABLE order_imports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  status import_status NOT NULL DEFAULT 'pending',
  total_rows INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
  imported_rows INTEGER NOT NULL DEFAULT 0 CHECK (imported_rows >= 0),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_order_id TEXT UNIQUE,
  import_id UUID REFERENCES order_imports(id) ON DELETE SET NULL,
  delivery_type_id UUID NOT NULL REFERENCES delivery_types(id),
  status order_status NOT NULL DEFAULT 'new',
  priority INTEGER NOT NULL DEFAULT 0,
  customer_name TEXT NOT NULL,
  required_weight_kg NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (required_weight_kg >= 0),
  required_volume_m3 NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (required_volume_m3 >= 0),
  time_window_start TIMESTAMPTZ,
  time_window_end TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  cancelled_at TIMESTAMPTZ,
  CHECK (time_window_end IS NULL OR time_window_start IS NULL OR time_window_end > time_window_start)
);

CREATE TABLE stops (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  kind stop_kind NOT NULL,
  address_line1 TEXT NOT NULL,
  address_line2 TEXT,
  city TEXT NOT NULL,
  region TEXT,
  postal_code TEXT,
  country TEXT NOT NULL DEFAULT 'Canada',
  latitude NUMERIC(9, 6),
  longitude NUMERIC(9, 6),
  earliest_at TIMESTAMPTZ,
  latest_at TIMESTAMPTZ,
  service_minutes INTEGER CHECK (service_minutes IS NULL OR service_minutes >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (order_id, kind),
  CHECK (latest_at IS NULL OR earliest_at IS NULL OR latest_at > earliest_at)
);

CREATE TABLE dispatch_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL DEFAULT 'Dispatch Session',
  active_plan_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ
);

CREATE TABLE dispatch_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES dispatch_sessions(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  is_current BOOLEAN NOT NULL DEFAULT false,
  source TEXT NOT NULL DEFAULT 'manual',
  total_distance_meters INTEGER NOT NULL DEFAULT 0 CHECK (total_distance_meters >= 0),
  total_travel_seconds INTEGER NOT NULL DEFAULT 0 CHECK (total_travel_seconds >= 0),
  total_dwell_seconds INTEGER NOT NULL DEFAULT 0 CHECK (total_dwell_seconds >= 0),
  total_schedule_seconds INTEGER NOT NULL DEFAULT 0 CHECK (total_schedule_seconds >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  approved_at TIMESTAMPTZ
);

ALTER TABLE dispatch_sessions
  ADD CONSTRAINT fk_dispatch_sessions_active_plan
  FOREIGN KEY (active_plan_id) REFERENCES dispatch_plans(id) ON DELETE SET NULL;

CREATE UNIQUE INDEX uq_dispatch_plans_one_current_per_session
  ON dispatch_plans(session_id)
  WHERE is_current;

CREATE TABLE routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES dispatch_plans(id) ON DELETE CASCADE,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
  status route_status NOT NULL DEFAULT 'draft',
  route_date DATE NOT NULL,
  starts_at TIMESTAMPTZ,
  ends_at TIMESTAMPTZ,
  distance_meters INTEGER NOT NULL DEFAULT 0 CHECK (distance_meters >= 0),
  travel_seconds INTEGER NOT NULL DEFAULT 0 CHECK (travel_seconds >= 0),
  dwell_seconds INTEGER NOT NULL DEFAULT 0 CHECK (dwell_seconds >= 0),
  geometry JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at)
);

CREATE TABLE route_stops (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  route_id UUID NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  stop_id UUID NOT NULL REFERENCES stops(id) ON DELETE CASCADE,
  sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),
  planned_arrival_at TIMESTAMPTZ,
  planned_departure_at TIMESTAMPTZ,
  actual_arrival_at TIMESTAMPTZ,
  actual_departure_at TIMESTAMPTZ,
  travel_seconds_from_previous INTEGER CHECK (travel_seconds_from_previous IS NULL OR travel_seconds_from_previous >= 0),
  distance_meters_from_previous INTEGER CHECK (distance_meters_from_previous IS NULL OR distance_meters_from_previous >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (route_id, sequence_number),
  UNIQUE (route_id, stop_id),
  CHECK (planned_departure_at IS NULL OR planned_arrival_at IS NULL OR planned_departure_at >= planned_arrival_at),
  CHECK (actual_departure_at IS NULL OR actual_arrival_at IS NULL OR actual_departure_at >= actual_arrival_at)
);

CREATE TABLE assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plan_id UUID NOT NULL REFERENCES dispatch_plans(id) ON DELETE CASCADE,
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
  route_id UUID REFERENCES routes(id) ON DELETE SET NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  unassigned_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (plan_id, order_id)
);

CREATE TABLE conversation_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES dispatch_sessions(id) ON DELETE CASCADE,
  role message_role NOT NULL,
  content TEXT NOT NULL,
  detected_intent TEXT,
  gemini_called BOOLEAN NOT NULL DEFAULT false,
  tool_calls JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dispatch_memory_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES dispatch_sessions(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES dispatch_plans(id) ON DELETE SET NULL,
  summary TEXT NOT NULL,
  state JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dispatch_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES dispatch_sessions(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES dispatch_plans(id) ON DELETE SET NULL,
  order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
  driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
  recommendation_id UUID,
  event_type TEXT NOT NULL,
  title TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES dispatch_sessions(id) ON DELETE CASCADE,
  current_plan_id UUID REFERENCES dispatch_plans(id) ON DELETE SET NULL,
  proposed_plan_id UUID REFERENCES dispatch_plans(id) ON DELETE SET NULL,
  status recommendation_status NOT NULL DEFAULT 'proposed',
  title TEXT NOT NULL,
  reason TEXT NOT NULL,
  affected_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
  from_driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  to_driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
  time_saved_seconds INTEGER NOT NULL DEFAULT 0,
  distance_saved_meters INTEGER NOT NULL DEFAULT 0,
  operational_benefits JSONB NOT NULL DEFAULT '[]'::jsonb,
  rejection_fingerprint TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at TIMESTAMPTZ,
  applied_at TIMESTAMPTZ,
  undone_at TIMESTAMPTZ
);

CREATE TABLE recommendation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_id UUID NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE dispatch_events
  ADD CONSTRAINT fk_dispatch_events_recommendation
  FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE SET NULL;

CREATE INDEX ix_orders_status ON orders(status);
CREATE INDEX ix_orders_priority ON orders(priority DESC);
CREATE INDEX ix_stops_location ON stops(latitude, longitude);
CREATE INDEX ix_driver_vehicle_assignments_driver ON driver_vehicle_assignments(driver_id);
CREATE INDEX ix_driver_vehicle_assignments_vehicle ON driver_vehicle_assignments(vehicle_id);
CREATE INDEX ix_routes_plan_id ON routes(plan_id);
CREATE INDEX ix_routes_driver_id ON routes(driver_id);
CREATE INDEX ix_route_stops_route_id ON route_stops(route_id);
CREATE INDEX ix_assignments_driver_id ON assignments(driver_id);
CREATE INDEX ix_messages_session_id_created_at ON conversation_messages(session_id, created_at);
CREATE INDEX ix_dispatch_events_session_created_at ON dispatch_events(session_id, created_at);
CREATE INDEX ix_dispatch_events_type ON dispatch_events(event_type);
CREATE INDEX ix_recommendations_session_status ON recommendations(session_id, status);
CREATE INDEX ix_recommendations_rejection_fingerprint ON recommendations(session_id, rejection_fingerprint)
  WHERE status = 'rejected' AND rejection_fingerprint IS NOT NULL;

INSERT INTO delivery_types (code, name, dwell_minutes)
VALUES
  ('curbside', 'Curbside', 10),
  ('threshold', 'Threshold', 20),
  ('white_glove', 'White Glove', 45)
ON CONFLICT (code) DO NOTHING;
