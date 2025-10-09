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

    def _create_fill(
        self,
        fill_id: str,
        price: float,
        quantity: float,
        timestamp: int,
        fee: float = 0.0,
        extra: dict | None = None,
    ) -> "FilledOrder":
        """[내부용] FilledOrder 객체만 생성 (상태 변경 없음)

        Args:
            fill_id: 체결 고유 ID
            price: 체결 가격
            quantity: 체결 수량
            timestamp: 체결 시각
            fee: 수수료 (기본값 0.0)
            extra: 거래소 특화 필드

        Returns:
            FilledOrder: 생성된 체결 기록

        Note:
            이 메서드는 내부용입니다. 일반 사용자는 process_fill()을 사용하세요.
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

    def process_fill(
        self,
        fill_id: str,
        price: float,
        quantity: float,
        timestamp: int,
        fee: float = 0.0,
        extra: dict | None = None,
    ) -> "FilledOrder":
        """체결 처리: FilledOrder 생성 + 상태 자동 업데이트

        이 메서드는 체결을 처리하고 자동으로 주문 상태를 업데이트합니다:
        1. FilledOrder 객체 생성
        2. filled_quantity 자동 증가
        3. 전량 체결 여부 확인
        4. 상태 자동 변경 (PARTIALLY_FILLED or FILLED)
        5. observers에게 알림

        Args:
            fill_id: 체결 고유 ID
            price: 체결 가격
            quantity: 체결 수량
            timestamp: 체결 시각
            fee: 수수료 (기본값 0.0)
            extra: 거래소 특화 필드

        Returns:
            FilledOrder: 생성된 체결 기록

        Raises:
            ValueError: 체결 수량이 남은 수량을 초과하는 경우
        """
        # 체결 수량 검증
        if quantity > self.remaining_quantity():
            raise ValueError(
                f"Fill quantity ({quantity}) exceeds remaining quantity "
                f"({self.remaining_quantity()})"
            )

        # FilledOrder 생성
        from .filled_order import FilledOrder

        filled_order = FilledOrder(
            order=self,
            fill_id=fill_id,
            price=price,
            quantity=quantity,
            timestamp=timestamp,
            fee=fee,
            extra=extra or {},
        )

        # filled_quantity 증가
        new_filled_quantity = self.filled_quantity + quantity

        # 상태 자동 결정
        if new_filled_quantity >= self.quantity:
            # 전량 체결
            new_status = OrderStatus.FILLED
        else:
            # 부분 체결
            new_status = OrderStatus.PARTIALLY_FILLED

        # 상태 업데이트 (observers에게 자동 알림)
        old_status = self.status
        self.filled_quantity = new_filled_quantity
        self.status = new_status

        # 모든 observers에게 알림
        for observer in self._observers:
            observer.on_order_status_changed(self, old_status, new_status)

        return filled_order
