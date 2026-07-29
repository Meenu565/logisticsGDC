from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1)
    tool_args: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)

