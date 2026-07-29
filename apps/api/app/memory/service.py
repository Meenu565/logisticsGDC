from uuid import UUID

from app.models import ConversationMessage, DispatchMemorySnapshot
from app.models.enums import MessageRole
from app.repositories.memory import ConversationRepository, MemorySnapshotRepository


class MemoryService:
    def __init__(
        self,
        conversations: ConversationRepository,
        snapshots: MemorySnapshotRepository,
    ) -> None:
        self.conversations = conversations
        self.snapshots = snapshots

    def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        detected_intent: str | None = None,
        gemini_called: bool = False,
        tool_calls: list[dict] | None = None,
    ) -> ConversationMessage:
        return self.conversations.add(
            ConversationMessage(
                session_id=session_id,
                role=role,
                content=content,
                detected_intent=detected_intent,
                gemini_called=gemini_called,
                tool_calls=tool_calls or [],
            )
        )

    def conversation_history(self, session_id: UUID, limit: int = 20) -> list[dict]:
        return [
            {
                "role": message.role.value,
                "content": message.content,
                "detected_intent": message.detected_intent,
                "gemini_called": message.gemini_called,
                "created_at": message.created_at.isoformat(),
            }
            for message in self.conversations.recent_messages(session_id, limit)
        ]

    def save_dispatch_state(
        self,
        session_id: UUID,
        summary: str,
        state: dict,
        plan_id: UUID | None = None,
    ) -> DispatchMemorySnapshot:
        return self.snapshots.add(
            DispatchMemorySnapshot(
                session_id=session_id,
                plan_id=plan_id,
                summary=summary,
                state=state,
            )
        )

    def latest_dispatch_state(self, session_id: UUID) -> dict | None:
        snapshot = self.snapshots.latest_for_session(session_id)
        if snapshot is None:
            return None
        return {
            "summary": snapshot.summary,
            "state": snapshot.state,
            "plan_id": str(snapshot.plan_id) if snapshot.plan_id else None,
            "created_at": snapshot.created_at.isoformat(),
        }

