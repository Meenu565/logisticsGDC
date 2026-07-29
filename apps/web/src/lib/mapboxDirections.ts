import type { Coordinate } from "../types/dispatch";

const token = import.meta.env.VITE_MAPBOX_TOKEN;

async function getSegment(
  from: Coordinate,
  to: Coordinate,
): Promise<Coordinate[]> {
  if (!token) return [from, to];

  const url =
    `https://api.mapbox.com/directions/v5/mapbox/driving-traffic/` +
    `${from.longitude},${from.latitude};${to.longitude},${to.latitude}` +
    `?overview=full` +
    `&geometries=geojson` +
    `&access_token=${token}`;

  const response = await fetch(url);

  if (!response.ok) {
    return [from, to];
  }

  const json = await response.json();

  return json.routes[0].geometry.coordinates.map(
    ([lng, lat]: [number, number]) => ({
      latitude: lat,
      longitude: lng,
    }),
  );
}

export async function getRoadGeometry(
  stops: Coordinate[],
): Promise<Coordinate[]> {

  if (!token || stops.length < 2) return stops;

  const merged: Coordinate[] = [];

  for (let i = 0; i < stops.length - 1; i++) {

    const segment = await getSegment(
      stops[i],
      stops[i + 1],
    );

    if (i === 0) {
      merged.push(...segment);
    } else {
      merged.push(...segment.slice(1));
    }
  }

  return merged;
}
