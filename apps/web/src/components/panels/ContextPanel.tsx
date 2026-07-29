import { AnimatePresence, motion } from "framer-motion";
import { Clock, MapPin, Package, Route, Truck, UserRound } from "lucide-react";
import { Badge } from "../ui/badge";
import { formatDistance, formatMinutes } from "../../lib/utils";
import { useDispatchStore } from "../../store/useDispatchStore";
import type { DashboardState } from "../../types/dispatch";

export function ContextPanel({ dashboard }: { dashboard: DashboardState }) {
  const panel = useDispatchStore((state) => state.contextPanel);

  if (!panel) return null;
  const selectedDriverRoute =panel.kind === "driver"? dashboard.routes.find((r) => r.driverId === panel.driver.id): null;

  return (
    <aside className="h-full overflow-hidden rounded-[24px] border border-white/10 bg-[#080d18] p-4 shadow-soft">
      <AnimatePresence mode="wait">
        <motion.div
          key={panel.kind}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -12 }}
          transition={{ duration: 0.18 }}
          className="h-full overflow-y-auto pr-1"
        >
          {panel.kind === "recommendation" && (
            <div>
              <PanelHeader icon={Package} eyebrow="Recommendation" title={panel.recommendation.title} />
              <p className="mt-4 text-sm leading-6 text-slate-300">{panel.recommendation.summary}</p>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <Metric label="Time saved" value={formatMinutes(panel.recommendation.timeSavedSeconds)} />
                <Metric label="Distance saved" value={formatDistance(panel.recommendation.distanceSavedMeters)} />
              </div>
              <div className="mt-5 rounded-2xl bg-white/[0.045] p-4 text-sm text-slate-300">
                <div className="text-xs uppercase tracking-wide text-slate-500">Before vs After</div>
                <div className="mt-3 flex items-center justify-between gap-3 text-white">
                  <span>{panel.recommendation.fromDriver}</span>
                  <span className="text-blue-300">to</span>
                  <span>{panel.recommendation.toDriver}</span>
                </div>
                <div className="mt-3 text-xs text-slate-500">Affected route: {panel.recommendation.routeId}</div>
              </div>
              <div className="mt-4 rounded-2xl border border-blue-300/15 bg-blue-500/10 px-4 py-3 text-sm text-blue-100">
                Approve this plan from chat so the dispatcher conversation and workspace stay synchronized.
              </div>
            </div>
          )}

          {panel.kind === "route" && (
            <div>
              <PanelHeader icon={Route} eyebrow="Route" title="ETA timeline" />
              <div className="mt-5 grid grid-cols-2 gap-3">
                <Metric label="Travel" value={formatMinutes(panel.route.travelSeconds)} />
                <Metric label="Distance" value={formatDistance(panel.route.distanceMeters)} />
                <Metric label="Start" value={formatDateTime(panel.route.startsAt) ?? "Not scheduled"} />
                <Metric label="Complete" value={formatDateTime(panel.route.endsAt) ?? "Not scheduled"} />
              </div>
              <div className="mt-6 space-y-3">
                {panel.route.stops?.map((stop) => (
  <div
    key={stop.sequence}
    className="rounded-2xl border border-white/10 bg-white/[0.045] p-3"
  >
    <div className="flex items-center gap-3">

      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/20 text-sm font-semibold text-blue-200">
        {stop.sequence}
      </div>

      <div className="flex-1">

        <div className="font-medium text-white">
          {stop.label}
        </div>

        <div className="mt-1 text-xs text-slate-400">
          {stop.arrival
            ? `ETA ${new Date(stop.arrival).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}`
            : estimatedStopText(stop.sequence, panel.route)}
        </div>

      </div>

    </div>
  </div>
))}
                
              </div>
              <div className="mt-4 rounded-2xl bg-blue-500/10 px-4 py-3">

    <div className="text-xs uppercase tracking-wide text-blue-300">
        Route Summary
    </div>

    <div className="mt-3 flex justify-between">
        <span className="text-slate-400">
            Vehicle
        </span>

        <span className="text-white">
            {panel.route.vehicle ?? "Unassigned"}
        </span>
    </div>

    <div className="mt-2 flex justify-between">
        <span className="text-slate-400">
            Stops
        </span>

        <span className="text-white">
            {panel.route.stops?.length ?? 0}
        </span>
    </div>

    <div className="mt-2 flex justify-between">
        <span className="text-slate-400">
            Distance
        </span>

        <span className="text-white">
            {formatDistance(panel.route.distanceMeters)}
        </span>
    </div>

    <div className="mt-2 flex justify-between">
        <span className="text-slate-400">
            Driving Time
        </span>

        <span className="text-white">
            {formatMinutes(panel.route.travelSeconds)}
        </span>
    </div>

</div>
                       </div>
          )}

          {panel.kind === "driver" && (
            <div>
            
              <PanelHeader icon={Truck} eyebrow="Driver" title={panel.driver.name} />

              <div className="mt-5 flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/16 text-lg font-semibold text-blue-100">
                  {panel.driver.name.replace("Driver ", "")}
                </div>
                <div>
                  <Badge>{panel.driver.status.replace("_", " ")}</Badge>
                  
                  <div className="mt-2 text-sm text-slate-400">{assignedOrders(panel.driver.id, dashboard).length > 0 ? `${assignedOrders(panel.driver.id, dashboard).length} stops assigned`: "No active route"}</div>

                </div>
              </div>
              <div className="mt-5 space-y-3 text-sm text-slate-300">
                <Row label="Vehicle" value={panel.driver.vehicle} />
                <Row label="Capacity" value={panel.driver.capacity} />
                <Row label="Remaining shift" value={`Until ${panel.driver.shiftEndsAt}`} />
                {selectedDriverRoute && (
  <>
    <div className="mt-6 border-t border-white/10 pt-5">
      <div className="text-xs uppercase tracking-wider text-slate-500">
        Current Route
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3">
        <Metric
          label="Travel"
          value={formatMinutes(selectedDriverRoute.travelSeconds)}
        />

        <Metric
          label="Distance"
          value={formatDistance(selectedDriverRoute.distanceMeters)}
        />
      </div>

      <div className="mt-5 space-y-2">
        {selectedDriverRoute.stopLabels.map((stop, index) => (
          <div
            key={stop}
            className="rounded-xl bg-white/[0.04] p-3 text-sm text-slate-200"
          >
            {index + 1}. {stop}
          </div>
        ))}
      </div>
    </div>
  </>
)}
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {panel.driver.qualification.map((item) => (
                  <Badge key={item}>{item}</Badge>
                ))}
              </div>
            </div>
          )}

          {panel.kind === "order" && (
            <div>
              <PanelHeader icon={Package} eyebrow="Order" title={panel.order.label} />
              <div className="mt-5 space-y-3 text-sm text-slate-300">
                <Row label="Customer" value={panel.order.customer} />
                <Row label="Priority" value={panel.order.priority} />
                <Row label="Delivery type" value={panel.order.type} />
                <Row label="Window" value={panel.order.window} />
                <Row label="Assigned driver" value={driverForOrder(panel.order.label, dashboard)} />
              </div>
              <LocationBlock label="Pickup" coordinate={panel.order.pickup} />
              <LocationBlock label="Dropoff" coordinate={panel.order.dropoff} />
            </div>
          )}

          {panel.kind === "eta" && (
            <div>
              <PanelHeader icon={Clock} eyebrow="ETA" title={panel.title} />
              <div className="mt-5 space-y-3">
                {panel.items.map((item) => (
                  <div key={item} className="rounded-2xl bg-white/[0.045] px-4 py-3 text-sm text-slate-300">
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
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-blue-300">
        <Icon className="h-4 w-4" />
        {eyebrow}
      </div>
      <h2 className="mt-3 text-xl font-semibold leading-7 text-white">{title}</h2>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white/[0.045] p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3 rounded-2xl bg-white/[0.045] px-4 py-3">
      <span className="text-slate-500">{label}</span>
      <span className="text-right text-white">{value}</span>
    </div>
  );
}

function LocationBlock({ label, coordinate }: { label: string; coordinate: { latitude: number; longitude: number } | null }) {
  return (
    <div className="mt-4 rounded-2xl bg-white/[0.045] p-4">
      <div className="flex items-center gap-2 text-sm text-slate-200">
        <MapPin className="h-4 w-4 text-blue-200" />
        {label}
      </div>
      <div className="mt-2 text-xs text-slate-500">
        {coordinate ? `${coordinate.latitude.toFixed(4)}, ${coordinate.longitude.toFixed(4)}` : "No coordinates"}
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
  if (!stopCount || !route.travelSeconds) return "ETA pending from route engine";
  const minutes = Math.max(1, Math.round((route.travelSeconds / stopCount / 60) * sequence));
  return `Estimated +${minutes} min from route start`;
}

function formatDateTime(value?: string | null) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* function assignedOrders(driverId: string, dashboard: DashboardState) {
  const route = dashboard.routes.find((item) => item.driverId === driverId);
  return route?.stopLabels.filter((label) => label.startsWith("Order")) ?? [];
}
*/

function driverForOrder(orderLabel: string, dashboard: DashboardState) {
  const route = dashboard.routes.find((item) => item.stopLabels.includes(orderLabel));
  const driver = dashboard.drivers.find((item) => item.id === route?.driverId);
  return driver?.name ?? "Unassigned";
}
