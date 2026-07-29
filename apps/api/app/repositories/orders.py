from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import cast, Integer, select

from app.models import DeliveryType, Order, OrderImport, Stop
from app.models.enums import ImportStatus
from app.models.enums import OrderStatus
from app.repositories.base import Repository


class OrderRepository(Repository[Order]):
    model = Order

    def list_active(self) -> Sequence[Order]:
        statement = (
            select(Order)
            .where(Order.status != OrderStatus.CANCELLED)
            .order_by(Order.priority.desc(), Order.created_at.asc())
        )
        return self.db.scalars(statement).all()

    def cancel_active(self) -> int:
        orders = list(self.list_active())
        for order in orders:
            order.status = OrderStatus.CANCELLED
            self.db.add(order)
        self.db.flush()
        return len(orders)

    def list_by_ids(self, order_ids: list[UUID]) -> Sequence[Order]:
        if not order_ids:
            return []
        statement = select(Order).where(Order.id.in_(order_ids))
        return self.db.scalars(statement).all()

    def list_external_numeric_range(self, start: int, end: int) -> Sequence[Order]:
        statement = (
            select(Order)
            .where(cast(Order.external_order_id, Integer).between(start, end))
            .order_by(cast(Order.external_order_id, Integer).asc())
        )
        return self.db.scalars(statement).all()

    def add_stop(self, stop: Stop) -> Stop:
        self.db.add(stop)
        self.db.flush()
        return stop

    def add_import(self, order_import: OrderImport) -> OrderImport:
        self.db.add(order_import)
        self.db.flush()
        return order_import

    def complete_import(
        self,
        order_import: OrderImport,
        imported_rows: int,
        status: ImportStatus = ImportStatus.COMPLETED,
        error_message: str | None = None,
    ) -> OrderImport:
        order_import.imported_rows = imported_rows
        order_import.status = status
        order_import.error_message = error_message
        self.db.add(order_import)
        self.db.flush()
        return order_import

    def get_delivery_type_by_code(self, code: str) -> DeliveryType | None:
        statement = select(DeliveryType).where(DeliveryType.code == code)
        return self.db.scalars(statement).one_or_none()
