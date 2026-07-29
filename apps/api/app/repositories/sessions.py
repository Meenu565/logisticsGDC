from app.models import DispatchSession
from app.repositories.base import Repository


class DispatchSessionRepository(Repository[DispatchSession]):
    model = DispatchSession

