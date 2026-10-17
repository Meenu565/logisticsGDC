import { AnimatePresence, motion } from "framer-motion";
import { Clock, MapPin, Package, Route, Truck, UserRound } from "lucide-react";
import { Badge } from "../ui/badge";
import { formatDistance, formatMinutes } from "../../lib/utils";
import { useDispatchStore } from "../../store/useDispatchStore";
import type { DashboardState } from "../../types/dispatch";

export function ContextPanel({ dashboard }: { dashboard: DashboardState }) {
  const panel = useDispatchStore((state) => state.contextPanel);

  if (!panel) return null;
  const selectedDriverRoute = panel.kind === "driver" ? dashboard.routes.find((r) => r.driverId === panel.driver.id) : null;

  return (
    <aside className="h-full overflow-hidden rounded-3xl border border-stone-800/80 bg-[#141211] p-4 shadow-card">
      <AnimatePresence mode="wait">
        <motion.div
          key={panel.kind}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -8 }}
          transition={{ duration: 0.16 }}
          className="h-full overflow-y-auto pr-1 scrollbar-soft"
        >
          {panel.kind === "recommendation" && (
            <div>
              <PanelHeader icon={Package} eyebrow="Recommendation" title={panel.recommendation.title} />
              <p className="mt-3 text-xs leading-5 text-stone-400">{panel.recommendation.summary}</p>
              
              <div className="mt-4 grid grid-cols-2 gap-2">
                <Metric label="Time saved" value={formatMinutes(panel.recommendation.timeSavedSeconds)} />
                <Metric label="Distance saved" value={formatDistance(panel.recommendation.distanceSavedMeters)} />
              </div>

              <div className="mt-4 rounded-2xl border border-stone-800 bg-[#191715] p-3 text-xs text-stone-300">
                <div className="text-[10px] uppercase tracking-wider text-stone-500 font-medium">Reassignment Plan</div>
                <div className="mt-2.5 flex items-center justify-between text-stone-100 font-medium">
                  <span>{panel.recommendation.fromDriver}</span>
                  <span className="text-purple-300">→</span>
                  <span>{panel.recommendation.toDriver}</span>
                </div>
                <div className="mt-2 text-[11px] text-stone-500">Route: {panel.recommendation.routeId}</div>
              </div>

              <div className="mt-3 rounded-2xl border border-purple-500/20 bg-purple-500/5 px-3 py-2 text-[11px] text-purple-200">
                Say "apply this plan" or click below to synchronize dispatch orders.
              </div>
            </div>
          )}

          {panel.kind === "route" && (
            <div>
              <PanelHeader icon={Route} eyebrow="Route" title="ETA Timeline" />
              <div className="mt-4 grid grid-cols-2 gap-2">
                <Metric label="Travel" value={formatMinutes(panel.route.travelSeconds)} />
                <Metric label="Distance" value={formatDistance(panel.route.distanceMeters)} />
                <Metric label="Start" value={formatDateTime(panel.route.startsAt) ?? "Not scheduled"} />
                <Metric label="Complete" value={formatDateTime(panel.route.endsAt) ?? "Not scheduled"} />
              </div>

              <div className="mt-5 space-y-2">
                {panel.route.stops?.map((stop) => (
                  <div key={stop.sequence} className="rounded-2xl border border-stone-800 bg-[#191715] p-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-stone-800 text-[10px] font-bold text-stone-300 border border-stone-700/60">
                        {stop.sequence}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-xs font-medium text-stone-200">{stop.label}</div>
                        <div className="text-[10px] text-stone-500">
                          {stop.arrival
                            ? `ETA ${new Date(stop.arrival).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                            : estimatedStopText(stop.sequence, panel.route)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 rounded-2xl border border-stone-800 bg-[#191715] p-3 text-xs">
                <div className="text-[10px] uppercase tracking-wider text-stone-500 font-medium">Route Summary</div>
                <div className="mt-2 space-y-1.5 text-stone-300">
                  <div className="flex justify-between">
                    <span className="text-stone-500">Vehicle</span>
                    <span className="text-stone-200 font-medium">{panel.route.vehicle ?? "Unassigned"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500">Total Stops</span>
                    <span className="text-stone-200">{panel.route.stops?.length ?? 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500">Distance</span>
                    <span className="text-stone-200">{formatDistance(panel.route.distanceMeters)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500">Driving Time</span>
                    <span className="text-stone-200">{formatMinutes(panel.route.travelSeconds)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {panel.kind === "driver" && (
            <div>
              <PanelHeader icon={Truck} eyebrow="Driver Details" title={panel.driver.name} />

              <div className="mt-4 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-800 text-sm font-semibold text-stone-100 border border-stone-700/60 shadow-sm">
                  {panel.driver.name.split(" ").map((n: string) => n[0]).join("")}
                </div>
                <div>
                  <Badge variant="stone" className="capitalize">
                    {panel.driver.status.replace("_", " ")}
                  </Badge>
                  <div className="mt-1 text-xs text-stone-400">
                    {assignedOrders(panel.driver.id, dashboard).length > 0
                      ? `${assignedOrders(panel.driver.id, dashboard).length} stops assigned`
                      : "No active route"}
                  </div>
                </div>
              </div>

              <div className="mt-4 space-y-2 text-xs">
                <Row label="Vehicle" value={panel.driver.vehicle} />
                <Row label="Capacity" value={panel.driver.capacity} />
                <Row label="Shift Window" value={`Until ${panel.driver.shiftEndsAt}`} />
              </div>

              {selectedDriverRoute && (
                <div className="mt-4 border-t border-stone-800/80 pt-3">
                  <div className="text-[10px] uppercase tracking-wider text-stone-500 font-medium">Assigned Route</div>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <Metric label="Travel" value={formatMinutes(selectedDriverRoute.travelSeconds)} />
                    <Metric label="Distance" value={formatDistance(selectedDriverRoute.distanceMeters)} />
                  </div>
                  <div className="mt-3 space-y-1.5">
                    {selectedDriverRoute.stopLabels.map((stop, index) => (
                      <div key={stop} className="rounded-xl border border-stone-800/80 bg-stone-900/60 p-2 text-xs text-stone-300">
                        {index + 1}. {stop}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-4 flex flex-wrap gap-1.5">
                {panel.driver.qualification.map((item) => (
                  <Badge key={item} variant="stone" className="text-[10px]">
                    {item}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {panel.kind === "order" && (
            <div>
              <PanelHeader icon={Package} eyebrow="Order Details" title={panel.order.label} />
              <div className="mt-4 space-y-2 text-xs">
                <Row label="Customer" value={panel.order.customer} />
                <Row label="Priority" value={panel.order.priority} />
                <Row label="Delivery type" value={panel.order.type} />
                <Row label="Time Window" value={panel.order.window} />
                <Row label="Assigned Driver" value={driverForOrder(panel.order.label, dashboard)} />
              </div>
              <LocationBlock label="Pickup Location" coordinate={panel.order.pickup} />
              <LocationBlock label="Dropoff Destination" coordinate={panel.order.dropoff} />
            </div>
          )}

          {panel.kind === "eta" && (
            <div>
              <PanelHeader icon={Clock} eyebrow="ETA Predictions" title={panel.title} />
              <div className="mt-4 space-y-2">
                {panel.items.map((item) => (
                  <div key={item} className="rounded-2xl border border-stone-800 bg-[#191715] px-3.5 py-2.5 text-xs text-stone-300">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </aside>
  );
}

function PanelHeader({ icon: Icon, eyebrow, title }: { icon: typeof Package; eyebrow: string; title: string }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-stone-400 font-medium">
        <Icon className="h-3.5 w-3.5 text-purple-300" />
        <span>{eyebrow}</span>
      </div>
      <h2 className="mt-1.5 text-base font-medium tracking-tight text-stone-100">{title}</h2>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-stone-800 bg-[#191715] p-3">
      <div className="text-[10px] text-stone-500 font-medium">{label}</div>
      <div className="mt-0.5 truncate text-sm font-medium text-stone-100">{value}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2 rounded-xl border border-stone-800/80 bg-stone-900/50 px-3 py-2 text-xs">
      <span className="text-stone-500">{label}</span>
      <span className="text-right text-stone-200 font-medium">{value}</span>
    </div>
  );
}

function LocationBlock({ label, coordinate }: { label: string; coordinate: { latitude: number; longitude: number } | null }) {
  return (
    <div className="mt-3 rounded-2xl border border-stone-800 bg-[#191715] p-3">
      <div className="flex items-center gap-1.5 text-xs text-stone-300 font-medium">
        <MapPin className="h-3.5 w-3.5 text-purple-300" />
        <span>{label}</span>
      </div>
      <div className="mt-1.5 text-[11px] text-stone-500">
        {coordinate ? `${coordinate.latitude.toFixed(4)}, ${coordinate.longitude.toFixed(4)}` : "No coordinates set"}
      </div>
    </div>
  );
}

function assignedOrders(driverId: string, dashboard: DashboardState) {
  const route = dashboard.routes.find((item) => item.driverId === driverId);
  return route?.stopLabels ?? [];
}

function estimatedStopText(sequence: number, route: { travelSeconds: number; stops?: { sequence: number }[] }) {
  const stopCount = route.stops?.length ?? 0;
  if (!stopCount || !route.travelSeconds) return "ETA calculating...";
  const minutes = Math.max(1, Math.round((route.travelSeconds / stopCount / 60) * sequence));
  return `Estimated +${minutes} min from route start`;
}

function formatDateTime(value?: string | null) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function driverForOrder(orderLabel: string, dashboard: DashboardState) {
  const route = dashboard.routes.find((item) => item.stopLabels.includes(orderLabel));
  const driver = dashboard.drivers.find((item) => item.id === route?.driverId);
  return driver?.name ?? "Unassigned";
}
