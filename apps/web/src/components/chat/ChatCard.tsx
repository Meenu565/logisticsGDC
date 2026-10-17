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
  const Icon = icons[card.type] || Info;
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
      className="mt-2.5 cursor-pointer rounded-2xl border border-stone-800 bg-[#191715] p-3.5 transition-all hover:border-stone-700 hover:bg-[#1f1c1a]"
    >
      <div className="flex gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-stone-800 text-purple-300 border border-stone-700/60">
          <Icon className="h-3.5 w-3.5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[13px] font-medium text-stone-100">{card.title}</span>
            <Badge variant="stone" className="text-[10px] py-0 px-2">
              {cardLabel(card.type)}
            </Badge>
          </div>
          <p className="mt-1 text-xs leading-5 text-stone-400">{card.description}</p>

          {recommendation && (
            <>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <Metric label="Strategy" value={recommendation.strategy ?? recommendation.title.replace(" dispatch strategy", "")} />
                <Metric label="Distance" value={recommendation.metrics?.["Estimated distance"] ?? formatDistance(recommendation.distanceSavedMeters)} />
                <Metric label="Travel time" value={recommendation.metrics?.["Estimated travel time"] ?? formatMinutes(recommendation.timeSavedSeconds)} />
                <Metric label="Orders" value={recommendation.metrics?.["Orders covered"] ?? (findOrders(card.title, dashboard).join(", ") || "Affected route")} />
              </div>
              {recommendation.benefits?.length ? (
                <div className="mt-2 text-[11px] leading-4 text-emerald-300/90">
                  <span className="font-medium text-emerald-200">Benefits:</span> {recommendation.benefits.join(" ")}
                </div>
              ) : null}
              {recommendation.risks?.length ? (
                <div className="mt-1 text-[11px] leading-4 text-stone-400">
                  <span className="font-medium text-stone-300">Risks:</span> {recommendation.risks.join(" ")}
                </div>
              ) : null}
              <div className="mt-2.5 rounded-xl border border-purple-500/20 bg-purple-500/5 px-2.5 py-1.5 text-[11px] text-purple-200">
                Reply or say "apply it" or "balanced" to approve this plan.
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
    <div className="rounded-xl border border-stone-800/80 bg-stone-900/60 px-2.5 py-1.5">
      <div className="text-[10px] text-stone-500">{label}</div>
      <div className="mt-0.5 truncate text-[11px] font-medium text-stone-200">{value}</div>
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
