from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .order_info import OrderInfo
    from ..stock_address import StockAddress


@dataclass(frozen=True)
class FilledOrder:
    """주문 체결 내역"""

    order: "OrderInfo"
    fill_id: str
    price: float
    quantity: float
    timestamp: int  # Unix timestamp (seconds)
    fee: float
    extra: dict = field(default_factory=dict)

    @property
    def order_id(self) -> str:
        """원본 주문 ID (편의 속성)"""
        return self.order.order_id

    @property
    def stock_address(self) -> "StockAddress":
        """자산 주소 (편의 속성)"""
        return self.order.stock_address
