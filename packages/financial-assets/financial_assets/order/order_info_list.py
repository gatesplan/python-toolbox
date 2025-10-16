from typing import TYPE_CHECKING

from .order_status import OrderStatus

if TYPE_CHECKING:
    from .order_info import OrderInfo


class OrderInfoList:
    """상태별 OrderInfo 관리 (시간순 정렬)"""

    def __init__(self):
        self._orders: dict[str, "OrderInfo"] = {}
        self._by_status: dict[OrderStatus, list[str]] = {
            status: [] for status in OrderStatus
        }

    def add(self, order: "OrderInfo") -> None:
        """OrderInfo 추가 및 observer 등록"""
        self._orders[order.order_id] = order
        self._by_status[order.status].append(order.order_id)
        self._sort_by_timestamp(order.status)

        # Observer 등록
        order.attach(self)

    def remove(self, order_id: str) -> None:
        """OrderInfo 제거 및 observer 해제"""
        if order_id not in self._orders:
            return

        order = self._orders.pop(order_id)
        self._by_status[order.status].remove(order_id)
        order.detach(self)

    def on_order_status_changed(
        self, order: "OrderInfo", old_status: OrderStatus, new_status: OrderStatus
    ) -> None:
        """OrderInfo 상태 변경 알림 처리 (리스트 간 이동)"""
        order_id = order.order_id

        # 이전 상태 리스트에서 제거
        if order_id in self._by_status[old_status]:
            self._by_status[old_status].remove(order_id)

        # 새 상태 리스트에 추가
        if order_id not in self._by_status[new_status]:
            self._by_status[new_status].append(order_id)
            self._sort_by_timestamp(new_status)

    def _sort_by_timestamp(self, status: OrderStatus) -> None:
        """해당 상태의 리스트를 timestamp 기준 정렬"""
        self._by_status[status].sort(key=lambda oid: self._orders[oid].timestamp)

    def get_by_status(self, status: OrderStatus) -> list["OrderInfo"]:
        """특정 상태의 OrderInfo들 (시간순)"""
        return [self._orders[oid] for oid in self._by_status[status]]

    def get_active(self) -> list["OrderInfo"]:
        """Active 주문들 (OPEN, PARTIALLY_FILLED)"""
        return self.get_by_status(OrderStatus.OPEN) + self.get_by_status(
            OrderStatus.PARTIALLY_FILLED
        )

    def get_completed(self) -> list["OrderInfo"]:
        """완료된 주문들 (FILLED, CANCELED, REJECTED, EXPIRED, FAILED)"""
        return (
            self.get_by_status(OrderStatus.FILLED)
            + self.get_by_status(OrderStatus.CANCELED)
            + self.get_by_status(OrderStatus.REJECTED)
            + self.get_by_status(OrderStatus.EXPIRED)
            + self.get_by_status(OrderStatus.FAILED)
        )

    def get(self, order_id: str) -> "OrderInfo | None":
        """order_id로 OrderInfo 조회"""
        return self._orders.get(order_id)

    def __len__(self) -> int:
        """전체 Order 수"""
        return len(self._orders)

    def __contains__(self, order_id: str) -> bool:
        """order_id 포함 여부"""
        return order_id in self._orders
