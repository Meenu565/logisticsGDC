import json
from typing import Any

from app.agent.prompt_loader import load_prompt
from app.agent.types import AgentPlan, AgentResult, AgentToolCall
from app.core.config import settings
from app.mcp.registry import available_tool_specs, execute_tool
from uuid import UUID

DETERMINISTIC_RESPONSE_TOOLS = {
    "optimize_routes",
    "generate_recommendations",
    "apply_recommendation",
    "accept_recommendation",
    "reject_recommendation",
    "undo_last_change",
    "load_orders",
    "load_order_range",
    "list_available_drivers",
    "get_driver_status",
}


class GeminiOrchestrator:
    """Gemini reasoning layer that only orchestrates MCP tools."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
    
    def run(
    self,
    session_id: UUID,
    user_message: str,
    dispatch_context: dict[str, Any] | None,
    recent_conversation: list[dict[str, Any]],
) -> AgentResult:
        if not self.api_key:
            return AgentResult(
                response="Gemini is not configured. Add GEMINI_API_KEY to enable reasoning requests.",
                tool_calls=[],
                tool_results=[],
            )
        
        dispatch_context = dispatch_context or {}
        dispatch_context["session_id"] = str(session_id)

        plan = self._plan_tool_calls(user_message, dispatch_context, recent_conversation)
        tool_results = [
            {
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
                "result": execute_tool(tool_call.tool_name, tool_call.arguments),
            }
            for tool_call in plan.tool_calls
        ]
        try:
            response = self._final_response(
                user_message=user_message,
                dispatch_context=dispatch_context,
                recent_conversation=recent_conversation,
                plan=plan,
                tool_results=tool_results,
            )
        except Exception:
            if self._has_successful_tool_result(tool_results):
                response = self._deterministic_response(tool_results)
            else:
                raise
        return AgentResult(
            response=response,
            tool_calls=[
                {"tool_name": tool_call.tool_name, "arguments": tool_call.arguments}
                for tool_call in plan.tool_calls
            ],
            tool_results=tool_results,
        )

    def summarize_tool_results(
        self,
        session_id: UUID,
        user_message: str,
        dispatch_context: dict[str, Any] | None,
        recent_conversation: list[dict[str, Any]],
        tool_results: list[dict[str, Any]],
        response_guidance: str = "",
    ) -> str:
        dispatch_context = dispatch_context or {}
        dispatch_context["session_id"] = str(session_id)
        if not self.api_key:
            return self._deterministic_response(tool_results)
        try:
            return self._final_response(
                user_message=user_message,
                dispatch_context=dispatch_context,
                recent_conversation=recent_conversation,
                plan=AgentPlan(tool_calls=[], response_guidance=response_guidance),
                tool_results=tool_results,
            )
        except Exception:
            if self._has_successful_tool_result(tool_results):
                return self._deterministic_response(tool_results)
            raise

    def _client(self):
        from google import genai

        return genai.Client(api_key=self.api_key)

    def _plan_tool_calls(
        self,
        user_message: str,
        dispatch_context: dict[str, Any] | None,
        recent_conversation: list[dict[str, Any]],
    ) -> AgentPlan:
        prompt = "\n\n".join(
            [
                load_prompt("system"),
                load_prompt("tool_selection"),
                self._json_section("Available MCP tools", available_tool_specs()),
                self._json_section("Latest dispatch state", dispatch_context),
                self._json_section("Recent conversation", recent_conversation[-8:]),
                f"User message:\n{user_message}",
            ]
        )
        response_text = self._generate_text(prompt)
        payload = self._parse_json(response_text)
        return AgentPlan(
            tool_calls=[
                AgentToolCall(
                    tool_name=item["tool_name"],
                    arguments=item.get("arguments", {}),
                )
                for item in payload.get("tool_calls", [])
                if item.get("tool_name")
            ],
            response_guidance=payload.get("response_guidance", ""),
        )

    def _final_response(
        self,
        user_message: str,
        dispatch_context: dict[str, Any] | None,
        recent_conversation: list[dict[str, Any]],
        plan: AgentPlan,
        tool_results: list[dict[str, Any]],
    ) -> str:
        prompt = "\n\n".join(
            [
                load_prompt("system"),
                load_prompt("recommendation"),
                load_prompt("final_response"),
                self._json_section("Latest dispatch state", dispatch_context),
                self._json_section("Recent conversation", recent_conversation[-8:]),
                self._json_section("Tool plan", {"response_guidance": plan.response_guidance}),
                self._json_section("Tool results", tool_results),
                f"User message:\n{user_message}",
            ]
        )
        return self._generate_text(prompt).strip()
    
    def _generate_text(self, prompt: str) -> str:
        try:
            client = self._client()

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            return response.text or ""

        except Exception:
            raise

    #def _generate_text(self, prompt: str) -> str:
        #response = self._client().models.generate_content(
        #    model=self.model,
       #     contents=prompt,
       # )
       # return response.text or ""

    def _parse_json(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"tool_calls": [], "response_guidance": cleaned}
        return parsed if isinstance(parsed, dict) else {"tool_calls": [], "response_guidance": ""}

    def _json_section(self, title: str, value: Any) -> str:
        return f"{title}:\n{json.dumps(value, indent=2, default=str)}"

    def _can_answer_deterministically(self, tool_results: list[dict[str, Any]]) -> bool:
        if not tool_results:
            return False
        return all(item.get("tool_name") in DETERMINISTIC_RESPONSE_TOOLS for item in tool_results)

    def _has_successful_tool_result(self, tool_results: list[dict[str, Any]]) -> bool:
        return any(item.get("result", {}).get("success") for item in tool_results)

    def _deterministic_response(self, tool_results: list[dict[str, Any]]) -> str:
        failed = [item for item in tool_results if not item.get("result", {}).get("success")]
        successful = [item for item in tool_results if item.get("result", {}).get("success")]
        if successful:
            return self._tool_summary(successful)
        if failed:
            return f"I could not complete that: {failed[0].get('result', {}).get('error', 'Unknown error')}"
        return "Done."

    def _tool_summary(self, tool_results: list[dict[str, Any]]) -> str:
        last = tool_results[-1]
        tool_name = last.get("tool_name")
        result = last.get("result", {})
        data = result.get("data", {})

        generated = next(
            (
                item
                for item in tool_results
                if item.get("tool_name") == "generate_recommendations"
                and item.get("result", {}).get("data", {}).get("recommendation")
            ),
            None,
        )
        if generated:
            recommendation = generated["result"]["data"]["recommendation"]
            return (
                f"Recommendation generated: {recommendation.get('title', 'Use the optimized dispatch plan')}. "
                f"Time saved: {self._minutes(recommendation.get('time_saved_seconds', 0))}. "
                f"Distance saved: {self._km(recommendation.get('distance_saved_meters', 0))}. "
                "Reply yes to apply it."
            )
        if tool_name == "apply_recommendation":
            return "Recommendation applied successfully. The active dispatch plan has been updated."
        if tool_name == "reject_recommendation":
            return "Recommendation rejected. I will not apply that dispatch plan."
        if tool_name == "undo_last_change":
            return "Last applied recommendation undone. The dashboard has been updated."
        if tool_name == "optimize_routes":
            if data.get("recommendations"):
                recommendations = data.get("recommendations", [])
                names = [item.get("title", "Dispatch strategy").replace(" dispatch strategy", "") for item in recommendations]
                metrics = []
                for strategy in data.get("strategies", []):
                    plan = strategy.get("plan", {})
                    metrics.append(
                        f"{strategy.get('strategy', 'Strategy')}: {self._km(plan.get('total_distance_meters', 0))}, "
                        f"{self._minutes(plan.get('total_travel_seconds', 0))}, "
                        f"{strategy.get('vehicles_used', 0)} vehicles, {strategy.get('orders_covered', 0)} orders"
                    )
                return (
                    "I prepared three dispatch strategies: "
                    f"{', '.join(names)}. "
                    f"{' '.join(metrics)} "
                    "Choose Fastest, Shortest, or Balanced to apply one plan."
                )
            plan = data.get("plan", {})
            return (
                "Routes optimized. "
                f"Total distance: {self._km(plan.get('total_distance_meters', 0))}. "
                f"Travel time: {self._minutes(plan.get('total_travel_seconds', 0))}. "
                f"Schedule duration: {self._minutes(plan.get('total_schedule_seconds', 0))}."
            )
        if tool_name in {"load_orders", "load_order_range"}:
            return self._orders_summary(data.get("orders", []))
        if tool_name == "list_available_drivers":
            return self._drivers_summary(data.get("drivers", []))
        return result.get("message") or "Done."

    def _orders_summary(self, orders: list[dict[str, Any]]) -> str:
        priority: dict[str, int] = {}
        statuses: dict[str, int] = {}
        delivery_types: dict[str, int] = {}
        for order in orders:
            priority[str(order.get("priority", "unknown"))] = priority.get(str(order.get("priority", "unknown")), 0) + 1
            statuses[str(order.get("status", "unknown"))] = statuses.get(str(order.get("status", "unknown")), 0) + 1
            delivery_type = order.get("delivery_type") or order.get("delivery_type_id") or "unknown"
            delivery_types[str(delivery_type)] = delivery_types.get(str(delivery_type), 0) + 1
        return (
            f"There are {len(orders)} active orders. "
            f"Priority breakdown: {self._breakdown(priority)}. "
            f"Dispatch status: {self._breakdown(statuses)}. "
            f"Delivery types: {self._breakdown(delivery_types)}."
        )

    def _drivers_summary(self, drivers: list[dict[str, Any]]) -> str:
        names = [driver.get("display_name") or driver.get("name") for driver in drivers]
        visible_names = ", ".join(str(name) for name in names[:5] if name)
        return f"{len(drivers)} drivers are available." + (f" Available now: {visible_names}." if visible_names else "")

    def _breakdown(self, values: dict[str, int]) -> str:
        return ", ".join(f"{key}: {value}" for key, value in values.items()) if values else "unavailable"

    def _minutes(self, seconds: Any) -> str:
        try:
            return f"{round(int(seconds) / 60)} min"
        except (TypeError, ValueError):
            return "unavailable"

    def _km(self, meters: Any) -> str:
        try:
            return f"{round(int(meters) / 1000, 1)} km"
        except (TypeError, ValueError):
            return "unavailable"
