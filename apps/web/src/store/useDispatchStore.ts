import { create } from "zustand";
import type { ChatCard, ChatMessage, ContextPanel, DashboardState, Driver, Order, Recommendation, Route } from "../types/dispatch";

type DispatchStore = {
  selectedRouteId: string | null;
  selectedDriverId: string | null;
  selectedOrderId: string | null;
  selectedRecommendationId: string | null;
  contextPanel: ContextPanel | null;
  messages: ChatMessage[];
  setMessages: (messages: ChatMessage[]) => void;
  appendMessage: (message: ChatMessage) => void;
  resetWorkspaceState: () => void;
  hydrateContext: (state: DashboardState) => void;
  selectRoute: (route: Route) => void;
  selectDriver: (driver: Driver, route?: Route) => void;
  selectOrder: (order: Order, route?: Route) => void;
  selectRecommendation: (recommendation: Recommendation) => void;
  syncFromMessage: (message: ChatMessage, dashboard: DashboardState) => void;
  syncFromCard: (card: ChatCard, dashboard: DashboardState) => void;
};

export const useDispatchStore = create<DispatchStore>((set) => ({
  selectedRouteId: null,
  selectedDriverId: null,
  selectedOrderId: null,
  selectedRecommendationId: null,
  contextPanel: null,
  messages: [],
  setMessages: (messages) => set({ messages }),
  appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  resetWorkspaceState: () =>
    set({
      selectedRouteId: null,
      selectedDriverId: null,
      selectedOrderId: null,
      selectedRecommendationId: null,
      contextPanel: null,
      messages: [],
    }),
  hydrateContext: (dashboard) =>
    set((state) => ({
      messages: dashboard.messages.length ? dashboard.messages : state.messages,
      contextPanel: dashboard.recommendations[0]
        ? { kind: "recommendation", recommendation: dashboard.recommendations[0] }
        : dashboard.orders[0]
          ? { kind: "order", order: dashboard.orders[0] }
          : dashboard.drivers[0]
            ? { kind: "driver", driver: dashboard.drivers[0] }
            : null,
      selectedRecommendationId: dashboard.recommendations[0]?.id ?? null,
      selectedRouteId: dashboard.recommendations[0]?.routeId ?? dashboard.routes[0]?.id ?? null,
      selectedDriverId: dashboard.recommendations[0]
        ? findDriverByName(dashboard, dashboard.recommendations[0].toDriver)?.id ?? null
        : dashboard.routes[0]?.driverId ?? null,
      selectedOrderId: findReferencedOrder(dashboard.recommendations[0]?.title ?? "", dashboard)?.id ?? null,
    })),
  selectRoute: (route) =>
    set({
      selectedRouteId: route.id,
      selectedDriverId: route.driverId,
      selectedRecommendationId: null,
      contextPanel: { kind: "route", route },
    }),
  selectDriver: (driver, route) =>
    set({
      selectedDriverId: driver.id,
      selectedRouteId: route?.id ?? null,
      selectedRecommendationId: null,
      contextPanel: { kind: "driver", driver },
    }),
  selectOrder: (order, route) =>
    set({
      selectedOrderId: order.id,
      selectedRouteId: route?.id ?? null,
      selectedRecommendationId: null,
      contextPanel: { kind: "order", order },
    }),
  selectRecommendation: (recommendation) =>
    set({
      selectedRecommendationId: recommendation.id,
      selectedRouteId: recommendation.routeId,
      selectedDriverId: null,
      selectedOrderId: findOrderIdFromText(recommendation.title),
      contextPanel: { kind: "recommendation", recommendation },
    }),
  syncFromMessage: (message, dashboard) => {
    const target = inferWorkspaceTarget(message.content, dashboard);
    set(target);
  },
  syncFromCard: (card, dashboard) => {
    const payloadRecommendation = card.payload?.recommendation as Recommendation | undefined;
    if (payloadRecommendation) {
      set({
        selectedRecommendationId: payloadRecommendation.id,
        selectedRouteId: payloadRecommendation.routeId,
        selectedDriverId: findDriverByName(dashboard, payloadRecommendation.toDriver)?.id ?? null,
        selectedOrderId: findReferencedOrder(payloadRecommendation.title, dashboard)?.id ?? null,
        contextPanel: { kind: "recommendation", recommendation: payloadRecommendation },
      });
      return;
    }
    const target = inferWorkspaceTarget(`${card.title} ${card.description}`, dashboard);
    set(target);
  },
}));

function inferWorkspaceTarget(text: string, dashboard: DashboardState) {
  const recommendation = dashboard.recommendations.find(
    (item) => textIncludes(text, item.id) || textIncludes(text, item.title) || textIncludes(text, "recommendation"),
  );
  if (recommendation) {
    return {
      selectedRecommendationId: recommendation.id,
      selectedRouteId: recommendation.routeId,
      selectedDriverId: findDriverByName(dashboard, recommendation.toDriver)?.id ?? null,
      selectedOrderId: findReferencedOrder(recommendation.title, dashboard)?.id ?? null,
      contextPanel: { kind: "recommendation", recommendation } as ContextPanel,
    };
  }

  const driver = dashboard.drivers.find((item) => textIncludes(text, item.name) || textIncludes(text, item.id));
  if (driver) {
    const route = dashboard.routes.find((item) => item.driverId === driver.id);
    return {
      selectedDriverId: driver.id,
      selectedRouteId: route?.id ?? null,
      selectedRecommendationId: null,
      contextPanel: { kind: "driver", driver } as ContextPanel,
    };
  }

  const order = findReferencedOrder(text, dashboard);
  if (order) {
    const route = dashboard.routes.find((item) => item.stopLabels.some((label) => label === order.label));
    return {
      selectedOrderId: order.id,
      selectedRouteId: route?.id ?? null,
      selectedRecommendationId: null,
      contextPanel: { kind: "order", order } as ContextPanel,
    };
  }

  const route = dashboard.routes.find((item) => textIncludes(text, item.id) || textIncludes(text, "route"));
  if (route) {
    return {
      selectedRouteId: route.id,
      selectedDriverId: route.driverId,
      selectedRecommendationId: null,
      contextPanel: { kind: "route", route } as ContextPanel,
    };
  }

  return {};
}

function findReferencedOrder(text: string, dashboard: DashboardState) {
  const orderId = findOrderIdFromText(text);
  return dashboard.orders.find((item) => item.id === orderId || textIncludes(text, item.label));
}

function findOrderIdFromText(text: string) {
  const match = text.match(/order\s*#?\s*(\d+)/i);
  return match ? `order-${match[1]}` : null;
}

function findDriverByName(dashboard: DashboardState, name: string) {
  return dashboard.drivers.find(
    (driver) => driver.name.toLowerCase() === name.toLowerCase() || driver.id.toLowerCase() === name.toLowerCase(),
  );
}

function textIncludes(text: string, value: string) {
  return text.toLowerCase().includes(value.toLowerCase());
}
