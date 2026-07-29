from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentToolCall:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentPlan:
    tool_calls: list[AgentToolCall]
    response_guidance: str


@dataclass(frozen=True)
class AgentResult:
    response: str
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]

