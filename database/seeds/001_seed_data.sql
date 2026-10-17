-- Seed delivery types
INSERT INTO delivery_types (id, code, name, dwell_minutes)
VALUES
  ('a0000000-0000-0000-0000-000000000001', 'curbside', 'Curbside', 10),
  ('a0000000-0000-0000-0000-000000000002', 'threshold', 'Threshold', 15),
  ('a0000000-0000-0000-0000-000000000003', 'white_glove', 'White Glove', 30)
ON CONFLICT (code) DO NOTHING;

-- Seed vehicles
INSERT INTO vehicles (id, label, status, capacity_weight_kg, capacity_volume_m3)
VALUES
  ('b0000000-0000-0000-0000-000000000001', 'Van-101 (Sprinter)', 'available', 1500.00, 12.00),
  ('b0000000-0000-0000-0000-000000000002', 'Van-102 (Transit)', 'available', 1400.00, 11.00),
  ('b0000000-0000-0000-0000-000000000003', 'Truck-201 (Box Truck)', 'available', 3500.00, 24.00)
ON CONFLICT DO NOTHING;

-- Seed drivers with coordinates (e.g. Toronto / GTA area)
INSERT INTO drivers (
  id, display_name, status, max_weight_kg, max_volume_m3,
  shift_start, shift_end,
  home_city, home_country,
  home_latitude, home_longitude,
  current_latitude, current_longitude
)
VALUES
  (
    'c0000000-0000-0000-0000-000000000001', 'Carlos Rodriguez', 'available', 1500.00, 12.00,
    now(), now() + interval '8 hours',
    'Toronto', 'Canada',
    43.653225, -79.383186,
    43.653225, -79.383186
  ),
  (
    'c0000000-0000-0000-0000-000000000002', 'Sarah Chen', 'available', 1400.00, 11.00,
    now(), now() + interval '8 hours',
    'North York', 'Canada',
    43.761539, -79.411079,
    43.761539, -79.411079
  ),
  (
    'c0000000-0000-0000-0000-000000000003', 'Marcus Johnson', 'available', 3500.00, 24.00,
    now(), now() + interval '8 hours',
    'Mississauga', 'Canada',
    43.589045, -79.644120,
    43.589045, -79.644120
  )
ON CONFLICT DO NOTHING;

-- Assign drivers to vehicles
INSERT INTO driver_vehicle_assignments (driver_id, vehicle_id)
VALUES
  ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001'),
  ('c0000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000002'),
  ('c0000000-0000-0000-0000-000000000003', 'b0000000-0000-0000-0000-000000000003')
ON CONFLICT DO NOTHING;
