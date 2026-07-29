import { Clock, Info, PackageCheck, Route, Sparkles, Truck, UploadCloud } from "lucide-react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { formatDistance, formatMinutes } from "../../lib/utils";
import { useDispatchStore } from "../../store/useDispatchStore";
import type { ChatCard as ChatCardType, DashboardState, Recommendation } from "../../types/dispatch";

const icons = {
  route_summary: Route,
  driver_assignment: Truck,
  optimization_complete: Sparkles,
  recommendation: PackageCheck,
  eta: Clock,
  import_success: UploadCloud,
  driver_info: Truck,
  order_info: Info,
};

export function ChatCard({ card, dashboard }: { card: ChatCardType; dashboard: DashboardState }) {
  const Icon = icons[card.type];
  const syncFromCard = useDispatchStore((state) => state.syncFromCard);
  const payloadRecommendation = card.payload?.recommendation as Recommendation | undefined;
  const recommendation =
    card.type === "recommendation"
      ? dashboard.recommendations.find((item) => item.id === payloadRecommendation?.id) ??
        payloadRecommendation ??
        dashboard.recommendations.find((item) => card.title.includes(item.title) || item.title.includes(card.title)) ??
        dashboard.recommendations[0]
      : null;
  

  return (
    <Card
      role="button"
      tabIndex={0}
      onClick={() => syncFromCard(card, dashboard)}
      onKeyDown={(event) => {
        if (event.key === "Enter") syncFromCard(card, dashboard);
      }}
      className="mt-3 cursor-pointer rounded-[18px] border-blue-300/14 bg-[#0d1728] p-4 transition hover:border-blue-300/35 hover:bg-[#101d31]"
    >
      <div className="flex gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-400/18 text-blue-200">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-semibold text-white">{card.title}</div>
            <Badge className="border-blue-300/15 bg-blue-400/10 text-blue-100">{cardLabel(card.type)}</Badge>
          </div>
          <p className="mt-1 text-sm leading-6 text-slate-300">{card.description}</p>

          {recommendation && (
            <>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <Metric label="Strategy" value={recommendation.strategy ?? recommendation.title.replace(" dispatch strategy", "")} />
                <Metric label="Distance" value={recommendation.metrics?.["Estimated distance"] ?? formatDistance(recommendation.distanceSavedMeters)} />
                <Metric label="Travel time" value={recommendation.metrics?.["Estimated travel time"] ?? formatMinutes(recommendation.timeSavedSeconds)} />
                <Metric label="Orders" value={recommendation.metrics?.["Orders covered"] ?? (findOrders(card.title, dashboard).join(", ") || "Affected route")} />
              </div>
              {recommendation.benefits?.length ? (
                <div className="mt-3 text-xs leading-5 text-slate-400">
                  <span className="font-medium text-slate-200">Benefits:</span> {recommendation.benefits.join(" ")}
                </div>
              ) : null}
              {recommendation.risks?.length ? (
                <div className="mt-1 text-xs leading-5 text-slate-500">
                  <span className="font-medium text-slate-300">Risks:</span> {recommendation.risks.join(" ")}
                </div>
              ) : null}
              <div className="mt-3 rounded-xl border border-blue-300/15 bg-blue-500/10 px-3 py-2 text-xs text-blue-100">
                Reply with Fastest, Shortest, Balanced, or "apply it" to approve through chat.
              </div>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/[0.045] px-3 py-2">
      <div className="text-[11px] text-slate-500">{label}</div>
      <div className="mt-0.5 truncate text-xs font-medium text-slate-100">{value}</div>
    </div>
  );
}

function cardLabel(type: ChatCardType["type"]) {
  return type
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function findOrders(text: string, dashboard: DashboardState) {
  return dashboard.orders.filter((order) => text.includes(order.label)).map((order) => order.label);
}
