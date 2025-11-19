"""Trade base data structure.

This module provides the Trade abstract base class for all trade types.
It defines common attributes and behavior shared by SpotTrade and FuturesTrade.
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from ..constants import OrderSide
from ..pair import Pair
from ..stock_address import StockAddress
from ..token import Token

if TYPE_CHECKING:
    from ..order import Order


@dataclass(frozen=True)
class Trade(ABC):
    """체결 완료된 거래의 추상 베이스 클래스 (불변 데이터 구조).
    모든 Trade 타입의 공통 속성과 동작을 정의합니다.
    """

    trade_id: str
    order: "Order"
    pair: Pair
    timestamp: int
    fee: Optional[Token] = None
    stock_address: StockAddress = field(init=False)
    side: OrderSide = field(init=False)

    def __post_init__(self):
        """order에서 stock_address와 side를 초기화."""
        object.__setattr__(self, "stock_address", self.order.stock_address)
        object.__setattr__(self, "side", self.order.side)
