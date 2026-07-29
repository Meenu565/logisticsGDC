import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent import GeminiOrchestrator
from app.intent.router import IntentContext, IntentKind, IntentRouter
from app.mcp.registry import execute_tool
from app.memory import MemoryService
from app.models.enums import MessageRole
from app.repositories.memory import ConversationRepository, MemorySnapshotRepository

logger = logging.getLogger("smart_dispatcher.conversation")

APPLY_PHRASES = {
    "yes",
    "y",
    "do that",
    "apply",
    "apply that",
    "apply it",
    "apply this",
    "apply this plan",
    "apply the plan",
    "yes apply it",
    "yes apply this plan",
    "proceed",
    "confirm",
    "finalize",
    "go ahead",
    "accept that",
    "accept it",
    "accept this plan",
}

REJECT_PHRASES = {
    "no",
    "reject",
    "don't suggest that again",
    "dont suggest that again",
    "reject that",
    "reject it",
    "reject this plan",
}


class ConversationOrchestrator:
    """Single request orchestration layer for dispatcher chat."""

    def __init__(
        self,
        db: Session,
        intent_router: IntentRouter | None = None,
        gemini: GeminiOrchestrator | None = None,
    ) -> None:
        self.db = db
        self.memory = MemoryService(
            conversations=ConversationRepository(db),
            snapshots=MemorySnapshotRepository(db),
        )
        self.intent_router = intent_router or IntentRouter()
        self.gemini = gemini or GeminiOrchestrator()

    def handle_message(
        self,
        session_id: UUID,
        user_message: str,
        tool_args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        selected_tools: list[dict[str, Any]] = []
        tool_results: list[dict[str, Any]] = []
        gemini_called = False
        memory_updated = False
        recommendation_generated = False
        final_response = ""

        try:
            context = self.memory.latest_dispatch_state(session_id)
            recent = self.memory.conversation_history(session_id, limit=12)
            effective_tool_args = self._with_memory_context(tool_args or {}, context)
            follow_up_tools = self._follow_up_tools(user_message, session_id, effective_tool_args)
            intent = self.intent_router.classify(
                user_message,
                IntentContext(session_id=str(session_id), tool_args=effective_tool_args),
            )

            self.memory.add_message(
                session_id=session_id,
                role=MessageRole.DISPATCHER,
                content=user_message,
                detected_intent=intent.name,
                gemini_called=False,
            )

            if self._is_apply_phrase(user_message) and not effective_tool_args.get("recommendation_id"):
                final_response = "There is no pending recommendation to apply. Run optimization first so I can generate a recommendation."
            elif follow_up_tools:
                for tool_call in follow_up_tools:
                    selected_tools.append(tool_call)
                    result = execute_tool(tool_call["tool_name"], tool_call["arguments"])
                    tool_results.append({**tool_call, "result": result})
                final_response = self._follow_up_response(tool_results)
            elif intent.kind == IntentKind.GREETING:
                final_response = "Hi. I am ready to help with dispatch planning."
            elif intent.kind == IntentKind.NEEDS_INPUT:
                final_response = f"I need {', '.join(intent.missing_fields)} to do that."
            elif intent.kind == IntentKind.DIRECT_TOOL and intent.direct_tool:
                selected_tools.append(
                    {
                        "tool_name": intent.direct_tool.tool_name,
                        "arguments": intent.direct_tool.arguments,
                    }
                )
                result = execute_tool(intent.direct_tool.tool_name, intent.direct_tool.arguments)
                tool_results.append(
                    {
                        "tool_name": intent.direct_tool.tool_name,
                        "arguments": intent.direct_tool.arguments,
                        "result": result,
                    }
                )
                if intent.direct_tool.tool_name == "optimize_routes":
                    recommendation_tool = self._recommendation_tool_after_optimize(
                        session_id,
                        effective_tool_args,
                        result,
                    )
                    if recommendation_tool:
                        selected_tools.append(recommendation_tool)
                        recommendation_result = execute_tool(
                            recommendation_tool["tool_name"],
                            recommendation_tool["arguments"],
                        )
                        tool_results.append({**recommendation_tool, "result": recommendation_result})
                recommendation_generated = intent.direct_tool.tool_name in {"generate_recommendations", "optimize_routes"}
                gemini_called = bool(self.gemini.api_key)
                final_response = self.gemini.summarize_tool_results(
                    session_id=session_id,
                    user_message=user_message,
                    dispatch_context=context,
                    recent_conversation=recent,
                    tool_results=tool_results,
                    response_guidance="Summarize the backend dispatch planning result in concise dispatcher sections.",
                )
            else:
                gemini_called = True
                agent_result = self.gemini.run(session_id=session_id,user_message=user_message,dispatch_context=context,recent_conversation=recent,)
                selected_tools.extend(agent_result.tool_calls)
                tool_results.extend(agent_result.tool_results)
                final_response = agent_result.response

            recommendation_generated = any(
                item.get("tool_name") in {"generate_recommendations", "optimize_routes"}
                and item.get("result", {}).get("success")
                and (
                    item.get("result", {}).get("data", {}).get("recommendation")
                    or item.get("result", {}).get("data", {}).get("recommendations")
                )
                for item in tool_results
            )

            self.memory.add_message(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=final_response,
                detected_intent=intent.name,
                gemini_called=gemini_called,
                tool_calls=selected_tools,
            )
            self.memory.save_dispatch_state(
                session_id=session_id,
                summary=self._memory_summary(user_message, final_response),
                state={
                    **self._carry_forward_state(context),
                    "last_intent": intent.name,
                    "selected_tools": selected_tools,
                    "tool_results": tool_results,
                    "gemini_called": gemini_called,
                    **self._state_from_tool_results(tool_results),
                },
            )
            memory_updated = True
            self.db.commit()

            return {
                "success": True,
                "message": final_response,
                "data": {
                    "intent": intent.name,
                    "gemini_called": gemini_called,
                    "selected_tools": selected_tools,
                    "tool_results": tool_results,
                    "recommendation_generated": recommendation_generated,
                },
            }
        except Exception as exc:
            self.db.rollback()
            final_response = str(exc)
            return {"success": False, "message": "Conversation failed.", "data": {"error": str(exc)}}
        finally:
            self._log_request(
                session_id=session_id,
                user_message=user_message,
                intent_name=locals().get("intent").name if "intent" in locals() else "not_classified",
                gemini_called=gemini_called,
                reason=locals().get("intent").reason if "intent" in locals() else "Exception before routing.",
                selected_tools=selected_tools,
                tool_results=tool_results,
                recommendation_generated=recommendation_generated,
                memory_updated=memory_updated,
                final_response=final_response,
                elapsed_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )

    def _direct_tool_response(self, tool_name: str, result: dict[str, Any]) -> str:
        if not result.get("success"):
            return f"I could not complete that: {result.get('error', 'Unknown error')}"
        return self._tool_summary([{"tool_name": tool_name, "result": result}])

    def _memory_summary(self, user_message: str, response: str) -> str:
        return f"User asked: {user_message}. Assistant responded: {response}"

    def _with_memory_context(
        self,
        tool_args: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        state = (context or {}).get("state", {})
        enriched = {**tool_args}
        if state.get("last_recommendation_id"):
            enriched.setdefault("recommendation_id", state["last_recommendation_id"])
        if state.get("recommendation_strategy_ids"):
            enriched.setdefault("recommendation_strategy_ids", state["recommendation_strategy_ids"])
        if state.get("current_plan_id"):
            enriched.setdefault("current_plan_id", state["current_plan_id"])
        if state.get("proposed_plan_id"):
            enriched.setdefault("proposed_plan_id", state["proposed_plan_id"])
        return enriched

    def _follow_up_tools(
        self,
        user_message: str,
        session_id: UUID,
        tool_args: dict[str, Any],
    ) -> list[dict[str, Any]]:
        normalized = " ".join(user_message.strip().lower().split())
        recommendation_id = self._recommendation_id_for_message(normalized, tool_args)
        if (normalized in APPLY_PHRASES or self._is_strategy_selection(normalized)) and recommendation_id:
            return [
                {
                    "tool_name": "accept_recommendation",
                    "arguments": {"recommendation_id": recommendation_id, "session_id": str(session_id)},
                },
                {
                    "tool_name": "apply_recommendation",
                    "arguments": {"recommendation_id": recommendation_id, "session_id": str(session_id)},
                },
            ]
        if normalized in REJECT_PHRASES and recommendation_id:
            return [
                {
                    "tool_name": "reject_recommendation",
                    "arguments": {"recommendation_id": recommendation_id, "reason": user_message},
                }
            ]
        if normalized in {"undo that", "undo the last change", "move it back"}:
            return [{"tool_name": "undo_last_change", "arguments": {"session_id": str(session_id)}}]
        return []

    def _is_strategy_selection(self, normalized: str) -> bool:
        return any(strategy in normalized for strategy in ("fastest", "shortest", "balanced"))

    def _recommendation_id_for_message(self, normalized: str, tool_args: dict[str, Any]) -> str | None:
        strategy_ids = tool_args.get("recommendation_strategy_ids") or {}
        if isinstance(strategy_ids, dict):
            if "fastest" in normalized:
                return strategy_ids.get("fastest route") or strategy_ids.get("fastest")
            if "shortest" in normalized:
                return strategy_ids.get("shortest route") or strategy_ids.get("shortest")
            if "balanced" in normalized:
                return strategy_ids.get("balanced route") or strategy_ids.get("balanced")
        return tool_args.get("recommendation_id")

    def _follow_up_response(self, tool_results: list[dict[str, Any]]) -> str:
        if any(not item["result"].get("success") for item in tool_results):
            failed = next(item for item in tool_results if not item["result"].get("success"))
            return f"I could not complete that: {failed['result'].get('error', 'Unknown error')}"
        return self._tool_summary(tool_results)

    def _carry_forward_state(self, context: dict[str, Any] | None) -> dict[str, Any]:
        return dict((context or {}).get("state", {}))

    def _state_from_tool_results(self, tool_results: list[dict[str, Any]]) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for item in tool_results:
            tool_name = item.get("tool_name")
            data = item.get("result", {}).get("data", {})
            recommendation = data.get("recommendation")
            recommendations = data.get("recommendations")
            plan = data.get("plan")
            if recommendations:
                strategy_ids: dict[str, str] = {}
                for recommendation_item in recommendations:
                    title = str(recommendation_item.get("title", "")).lower().replace(" dispatch strategy", "")
                    if title and recommendation_item.get("id"):
                        strategy_ids[title] = recommendation_item["id"]
                if strategy_ids:
                    state["recommendation_strategy_ids"] = strategy_ids
                    first_id = next(iter(strategy_ids.values()))
                    state["last_recommendation_id"] = strategy_ids.get("balanced route") or first_id
            if recommendation:
                if tool_name in {"apply_recommendation", "reject_recommendation", "undo_last_change"}:
                    state["last_recommendation_id"] = None
                    state["recommendation_strategy_ids"] = None
                    state["current_plan_id"] = None
                    state["proposed_plan_id"] = None
                else:
                    state["last_recommendation_id"] = recommendation.get("id")
                    state["current_plan_id"] = recommendation.get("current_plan_id")
                    state["proposed_plan_id"] = recommendation.get("proposed_plan_id")
            if plan:
                state["proposed_plan_id"] = plan.get("id")
        return state

    def _is_apply_phrase(self, user_message: str) -> bool:
        return " ".join(user_message.strip().lower().split()) in APPLY_PHRASES

    def _recommendation_tool_after_optimize(
        self,
        session_id: UUID,
        tool_args: dict[str, Any],
        optimize_result: dict[str, Any],
    ) -> dict[str, Any] | None:
        plan = optimize_result.get("data", {}).get("plan")
        current_plan_id = tool_args.get("current_plan_id")
        proposed_plan_id = plan.get("id") if isinstance(plan, dict) else None
        if not optimize_result.get("success") or not current_plan_id or not proposed_plan_id:
            return None
        if current_plan_id == proposed_plan_id:
            return None
        return {
            "tool_name": "generate_recommendations",
            "arguments": {
                "session_id": str(session_id),
                "current_plan_id": current_plan_id,
                "proposed_plan_id": proposed_plan_id,
            },
        }

    def _tool_summary(self, tool_results: list[dict[str, Any]]) -> str:
        if not tool_results:
            return "Done."
        last = tool_results[-1]
        tool_name = last.get("tool_name")
        result = last.get("result", {})
        data = result.get("data", {})

        if tool_name == "optimize_routes" and data.get("recommendations"):
            recommendations = data.get("recommendations", [])
            strategy_names = [item.get("title", "Dispatch strategy").replace(" dispatch strategy", "") for item in recommendations]
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
                f"{', '.join(strategy_names)}. "
                f"{' '.join(metrics)} "
                "Choose Fastest, Shortest, or Balanced to apply one plan."
            )

        if tool_name == "generate_recommendations" and data.get("recommendation"):
            recommendation = data["recommendation"]
            return (
                f"Recommendation generated: {recommendation.get('title', 'Use the optimized dispatch plan')}. "
                f"Time saved: {self._minutes(recommendation.get('time_saved_seconds', 0))}. "
                f"Distance saved: {self._km(recommendation.get('distance_saved_meters', 0))}. "
                "Reply yes to apply it."
            )
        if any(item.get("tool_name") == "generate_recommendations" for item in tool_results):
            generated = next(
                (item for item in tool_results if item.get("tool_name") == "generate_recommendations"),
                None,
            )
            recommendation = generated.get("result", {}).get("data", {}).get("recommendation") if generated else None
            if recommendation:
                return self._tool_summary([generated])

        if tool_name == "apply_recommendation":
            return "Recommendation applied successfully. The active dispatch plan has been updated."
        if tool_name == "reject_recommendation":
            return "Recommendation rejected. I will not apply that dispatch plan."
        if tool_name == "undo_last_change":
            return "Last applied recommendation undone. The dashboard has been updated."
        if tool_name == "optimize_routes":
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
        return result.get("message", "Done.")

    def _orders_summary(self, orders: list[dict[str, Any]]) -> str:
        total = len(orders)
        priority: dict[str, int] = {}
        statuses: dict[str, int] = {}
        delivery_types: dict[str, int] = {}
        for order in orders:
            priority[str(order.get("priority", "unknown"))] = priority.get(str(order.get("priority", "unknown")), 0) + 1
            statuses[str(order.get("status", "unknown"))] = statuses.get(str(order.get("status", "unknown")), 0) + 1
            delivery_type = order.get("delivery_type") or order.get("delivery_type_id") or "unknown"
            delivery_types[str(delivery_type)] = delivery_types.get(str(delivery_type), 0) + 1
        return (
            f"There are {total} active orders. "
            f"Priority breakdown: {self._breakdown(priority)}. "
            f"Dispatch status: {self._breakdown(statuses)}. "
            f"Delivery types: {self._breakdown(delivery_types)}."
        )

    def _drivers_summary(self, drivers: list[dict[str, Any]]) -> str:
        total = len(drivers)
        names = [driver.get("display_name") or driver.get("name") for driver in drivers]
        visible_names = ", ".join(str(name) for name in names[:5] if name)
        return f"{total} drivers are available." + (f" Available now: {visible_names}." if visible_names else "")

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

    def _log_request(
        self,
        session_id: UUID,
        user_message: str,
        intent_name: str,
        gemini_called: bool,
        reason: str,
        selected_tools: list[dict[str, Any]],
        tool_results: list[dict[str, Any]],
        recommendation_generated: bool,
        memory_updated: bool,
        final_response: str,
        elapsed_ms: float,
    ) -> None:
        logger.info(
            "\n".join(
                [
                    "[Conversation]",
                    f"Session: {session_id}",
                    f"User Message: {user_message}",
                    f"Intent: {intent_name}",
                    f"Gemini Called? {'YES' if gemini_called else 'NO'}",
                    f"Reason: {reason}",
                    f"Selected MCP Tools: {selected_tools}",
                    f"Tool Arguments: {[item.get('arguments') for item in selected_tools]}",
                    f"Tool Results: {tool_results}",
                    f"Recommendation Generated? {'YES' if recommendation_generated else 'NO'}",
                    f"Memory Updated? {'YES' if memory_updated else 'NO'}",
                    f"Final Response: {final_response}",
                    f"Execution Time: {elapsed_ms} ms",
                ]
            )
        )
