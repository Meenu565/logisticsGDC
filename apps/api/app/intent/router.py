import re
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


class IntentKind(StrEnum):
    GREETING = "greeting"
    DIRECT_TOOL = "direct_tool"
    GEMINI = "gemini"
    NEEDS_INPUT = "needs_input"


@dataclass(frozen=True)
class DirectToolRoute:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntentResult:
    kind: IntentKind
    name: str
    reason: str
    direct_tool: DirectToolRoute | None = None
    missing_fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IntentContext:
    session_id: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)


class IntentRouter:
    """Centralized deterministic router for requests that do not need Gemini."""

    greeting_phrases = {"hi", "hello", "hey", "good morning", "good afternoon"}
    reasoning_markers = {
        "why",
        "compare",
        "what happens if",
        "suggest",
        "better",
        "bottleneck",
        "should",
        "which driver",
        "can driver",
        "strategy",
        "explain",
    }

    def classify(self, message: str, context: IntentContext | None = None) -> IntentResult:
        context = context or IntentContext()
        normalized = self._normalize(message)

        if normalized in self.greeting_phrases:
            return IntentResult(IntentKind.GREETING, "greeting", "Matched greeting phrase.")

        direct = self._direct_route(normalized, context)
        if direct:
            return direct

        if any(marker in normalized for marker in self.reasoning_markers):
            return IntentResult(
                IntentKind.GEMINI,
                "dispatch_reasoning",
                "Request asks for reasoning, explanation, comparison, or recommendation strategy.",
            )

        return IntentResult(
            IntentKind.GEMINI,
            "unclassified_dispatch_request",
            "No deterministic route matched; Gemini should interpret the request.",
        )

    def _direct_route(self, normalized: str, context: IntentContext) -> IntentResult | None:
        if normalized in {"load orders", "show orders", "show today's orders", "list orders"}:
            return self._tool("load_orders", {"limit": context.tool_args.get("limit", 50)})

        range_match = re.search(r"(?:orders?|order range)\s+(\d+)\s*(?:-|to|through)\s*(\d+)", normalized)
        if range_match:
            return self._tool(
                "load_order_range",
                {"start": int(range_match.group(1)), "end": int(range_match.group(2))},
            )

        if normalized in {"list available drivers", "show available drivers", "available drivers"}:
            return self._tool("list_available_drivers", {})

        if "dispatch context" in normalized or "current context" in normalized:
            return self._session_tool("get_dispatch_context", context)

        if normalized.startswith("optimize routes") or normalized == "optimize today's routes":
            return self._session_tool(
                "optimize_routes",
                context,
                {"route_date": context.tool_args.get("route_date", date.today().isoformat())},
            )

        if normalized.startswith("generate recommendation"):
            return self._required_tool(
                "generate_recommendations",
                context,
                required=["session_id", "current_plan_id", "proposed_plan_id"],
            )

        if normalized.startswith("apply recommendation"):
            return self._required_tool(
                "apply_recommendation",
                context,
                required=["session_id", "recommendation_id"],
            )

        if normalized.startswith("accept recommendation"):
            return self._required_tool(
                "accept_recommendation",
                context,
                required=["recommendation_id"],
            )

        if normalized.startswith("reject recommendation"):
            return self._required_tool(
                "reject_recommendation",
                context,
                required=["recommendation_id"],
            )

        if normalized in {"undo that", "undo the last change", "move it back"}:
            return self._session_tool("undo_last_change", context)

        if normalized.startswith("calculate eta"):
            return self._required_tool("calculate_eta", context, required=["coordinates"])

        driver_status_match = re.search(r"driver\s+status\s+([0-9a-f-]{36})", normalized)
        if driver_status_match:
            return self._tool("get_driver_status", {"driver_id": driver_status_match.group(1)})

        return None

    def _tool(self, tool_name: str, arguments: dict[str, Any]) -> IntentResult:
        return IntentResult(
            kind=IntentKind.DIRECT_TOOL,
            name=tool_name,
            reason=f"Matched deterministic MCP tool: {tool_name}.",
            direct_tool=DirectToolRoute(tool_name=tool_name, arguments=arguments),
        )

    def _session_tool(
        self,
        tool_name: str,
        context: IntentContext,
        extra_args: dict[str, Any] | None = None,
    ) -> IntentResult:
        if not context.session_id:
            return IntentResult(
                kind=IntentKind.NEEDS_INPUT,
                name=tool_name,
                reason="Direct tool requires a session_id.",
                missing_fields=["session_id"],
            )
        return self._tool(tool_name, {"session_id": context.session_id, **(extra_args or {})})

    def _required_tool(
        self,
        tool_name: str,
        context: IntentContext,
        required: list[str],
    ) -> IntentResult:
        arguments = {**context.tool_args}
        if context.session_id and "session_id" in required:
            arguments.setdefault("session_id", context.session_id)
        missing = [field_name for field_name in required if not arguments.get(field_name)]
        if missing:
            return IntentResult(
                kind=IntentKind.NEEDS_INPUT,
                name=tool_name,
                reason=f"Direct tool requires fields: {', '.join(missing)}.",
                missing_fields=missing,
            )
        return self._tool(tool_name, arguments)

    def _normalize(self, message: str) -> str:
        return " ".join(message.strip().lower().split())
