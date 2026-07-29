from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models import ConversationMessage, DispatchMemorySnapshot
from app.repositories.base import Repository


class ConversationRepository(Repository[ConversationMessage]):
    model = ConversationMessage

    def recent_messages(self, session_id: UUID, limit: int = 20) -> Sequence[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        return list(reversed(self.db.scalars(statement).all()))


class MemorySnapshotRepository(Repository[DispatchMemorySnapshot]):
    model = DispatchMemorySnapshot

    def latest_for_session(self, session_id: UUID) -> DispatchMemorySnapshot | None:
        statement = (
            select(DispatchMemorySnapshot)
            .where(DispatchMemorySnapshot.session_id == session_id)
            .order_by(DispatchMemorySnapshot.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(statement).first()

