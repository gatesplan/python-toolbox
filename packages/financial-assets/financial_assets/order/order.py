from dataclasses import dataclass, field
from typing import Literal, TYPE_CHECKING
from ..stock_address import StockAddress
from .order_status import OrderStatus

if TYPE_CHECKING:
    from .filled_order import FilledOrder
    from .order_list import OrderList


@dataclass
class Order:
    """거래소 주문 정보를 표준화된 형식으로 보관하는 데이터 구조체"""

    stock_address: StockAddress
    order_id: str
    side: Literal["buy", "sell"]
    order_type: str
    price: float | None
    quantity: float
    filled_quantity: float
    status: OrderStatus
    timestamp: int  # Unix timestamp (seconds)
    extra: dict = field(default_factory=dict)
    _observers: list["OrderList"] = field(default_factory=list, repr=False, compare=False)

    def is_active(self) -> bool:
        """Active 상태 여부 (OPEN, PARTIALLY_FILLED)"""
        return self.status in {OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED}

    def is_completed(self) -> bool:
        """완료 상태 여부 (FILLED, CANCELED, REJECTED, EXPIRED, FAILED)"""
        return self.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.FAILED,
        }

    def remaining_quantity(self) -> float:
        """미체결 수량"""
        return self.quantity - self.filled_quantity

    def attach(self, observer: "OrderList") -> None:
        """OrderList observer 등록"""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: "OrderList") -> None:
        """OrderList observer 해제"""
        if observer in self._observers:
            self._observers.remove(observer)

    def update_status(self, new_status: OrderStatus) -> None:
        """상태 업데이트 및 observers 알림"""
        old_status = self.status
        self.status = new_status

        # 모든 observers에게 알림
        for observer in self._observers:
            observer.on_order_status_changed(self, old_status, new_status)

    def update_filled(self, filled_qty: float, new_status: OrderStatus) -> None:
        """체결 정보 업데이트 및 observers 알림"""
        old_status = self.status
        self.filled_quantity = filled_qty
        self.status = new_status

        # 모든 observers에게 알림
        for observer in self._observers:
            observer.on_order_status_changed(self, old_status, new_status)

    def create_fill(
        self,
        fill_id: str,
        price: float,
        quantity: float,
        timestamp: int,
        fee: float = 0.0,
        extra: dict | None = None,
    ) -> "FilledOrder":
        """이 주문의 체결 기록 생성

        Args:
            fill_id: 체결 고유 ID
            price: 체결 가격
            quantity: 체결 수량
            timestamp: 체결 시각
            fee: 수수료 (기본값 0.0)
            extra: 거래소 특화 필드

        Returns:
            FilledOrder: 생성된 체결 기록
        """
        from .filled_order import FilledOrder

        return FilledOrder(
            order=self,
            fill_id=fill_id,
            price=price,
            quantity=quantity,
            timestamp=timestamp,
            fee=fee,
            extra=extra or {},
        )
