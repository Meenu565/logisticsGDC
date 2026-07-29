from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models import DispatchEvent
from app.repositories.base import Repository


class DispatchEventRepository(Repository[DispatchEvent]):
    model = DispatchEvent

    def timeline(self, session_id: UUID, limit: int = 50) -> Sequence[DispatchEvent]:
        statement = (
            select(DispatchEvent)
            .where(DispatchEvent.session_id == session_id)
            .order_by(DispatchEvent.created_at.desc())
            .limit(limit)
        )
        return self.db.scalars(statement).all()
