from __future__ import annotations
from typing import Optional
from ..constants import Side, OrderStatus, TimeInForce
from ..stock_address import StockAddress
from simple_logger import init_logging, logger


class SpotOrder:
    """현물 거래 주문 (불변 복제 패턴).
    주문 정보, 체결 상태, 수수료, 최소 거래 제약을 캡슐화합니다.
    """

    @init_logging(level="INFO", log_params=True)
    def __init__(
        self,
        order_id: str,
        stock_address: StockAddress,
        side: Side,
        order_type: str,
        price: Optional[float],
        amount: float,
        timestamp: int,
        stop_price: Optional[float] = None,
        filled_amount: float = 0.0,
        status: OrderStatus = OrderStatus.PENDING,
        fee_rate: float = 0.0,
        min_trade_amount: Optional[float] = None,
        time_in_force: Optional[TimeInForce] = None,
        expire_timestamp: Optional[int] = None,
    ):
        """SpotOrder 초기화."""
        self.order_id = order_id
        self.stock_address = stock_address
        self.side = side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.filled_amount = filled_amount
        self.status = status
        self.timestamp = timestamp
        self.stop_price = stop_price
        self.fee_rate = fee_rate
        self.min_trade_amount = min_trade_amount
        self.time_in_force = time_in_force
        self.expire_timestamp = expire_timestamp

    def _clone(self, **overrides) -> SpotOrder:
        """속성을 덮어쓴 새 SpotOrder 복제."""
        return SpotOrder(
            order_id=overrides.get("order_id", self.order_id),
            stock_address=overrides.get("stock_address", self.stock_address),
            side=overrides.get("side", self.side),
            order_type=overrides.get("order_type", self.order_type),
            price=overrides.get("price", self.price),
            amount=overrides.get("amount", self.amount),
            timestamp=overrides.get("timestamp", self.timestamp),
            stop_price=overrides.get("stop_price", self.stop_price),
            filled_amount=overrides.get("filled_amount", self.filled_amount),
            status=overrides.get("status", self.status),
            fee_rate=overrides.get("fee_rate", self.fee_rate),
            min_trade_amount=overrides.get("min_trade_amount", self.min_trade_amount),
            time_in_force=overrides.get("time_in_force", self.time_in_force),
            expire_timestamp=overrides.get("expire_timestamp", self.expire_timestamp),
        )

    def fill_by_asset_amount(self, amount: float) -> SpotOrder:
        """자산 수량만큼 주문 체결."""
        logger.info(f"주문 체결 시작: order_id={self.order_id}, fill_amount={amount}")
        self._validate_fill(amount)

        new_filled = self.filled_amount + amount

        if new_filled >= self.amount:
            new_status = OrderStatus.FILLED
            logger.info(f"주문 완전 체결: order_id={self.order_id}, filled={new_filled}/{self.amount}")
        elif new_filled > 0:
            new_status = OrderStatus.PARTIAL
            logger.info(f"주문 부분 체결: order_id={self.order_id}, filled={new_filled}/{self.amount}")
        else:
            new_status = OrderStatus.PENDING

        return self._clone(filled_amount=new_filled, status=new_status)

    def fill_by_value_amount(self, amount: float) -> SpotOrder:
        """가치 금액만큼 주문 체결."""
        if self.price is None:
            raise ValueError("Cannot use fill_by_value_amount for market orders (price=None)")
        if self.price == 0:
            raise ValueError("Price cannot be zero for value-based fill")

        asset_amount = amount / self.price
        return self.fill_by_asset_amount(asset_amount)

    def remaining_asset(self) -> float:
        """미체결 자산 수량 반환."""
        return self.amount - self.filled_amount

    def remaining_value(self) -> float:
        """미체결 가치 금액 반환."""
        if self.price is None:
            raise ValueError("Cannot calculate remaining_value for market orders")
        return self.remaining_asset() * self.price

    def remaining_rate(self) -> float:
        if self.amount == 0:
            return 0.0
        return self.remaining_asset() / self.amount

    def is_filled(self) -> bool:
        """주문 완전 체결 여부."""
        return self.status == OrderStatus.FILLED

    def to_pending_state(self) -> SpotOrder:
        return self._clone(status=OrderStatus.PENDING)

    def to_partial_state(self) -> SpotOrder:
        return self._clone(status=OrderStatus.PARTIAL)

    def to_filled_state(self) -> SpotOrder:
        return self._clone(status=OrderStatus.FILLED)

    def to_canceled_state(self) -> SpotOrder:
        """주문을 취소 상태로 변경."""
        logger.info(f"주문 취소: order_id={self.order_id}, filled={self.filled_amount}/{self.amount}")
        return self._clone(status=OrderStatus.CANCELED)

    def is_remaining_below_min(self) -> bool:
        """잔여 수량이 최소 거래량 미만인지 확인."""
        if self.min_trade_amount is None:
            return False
        return self.remaining_asset() < self.min_trade_amount

    def _validate_fill(self, amount: float) -> None:
        """체결 수량 유효성 검증."""
        if self.status == OrderStatus.CANCELED:
            logger.error(f"취소된 주문 체결 시도: order_id={self.order_id}")
            raise ValueError("Cannot fill a canceled order")

        if amount < 0:
            logger.error(f"음수 체결 수량: order_id={self.order_id}, amount={amount}")
            raise ValueError("Fill amount cannot be negative")

        if self.filled_amount + amount > self.amount:
            logger.error(f"체결 수량 초과: order_id={self.order_id}, requested={amount}, remaining={self.remaining_asset()}")
            raise ValueError(
                f"Fill amount {amount} exceeds remaining amount {self.remaining_asset()}"
            )

        # Check minimum trade amount (but allow final fill even if below minimum)
        if self.min_trade_amount is not None:
            new_filled = self.filled_amount + amount
            is_complete_fill = new_filled >= self.amount

            if not is_complete_fill and amount < self.min_trade_amount:
                logger.error(
                    f"체결 수량이 최소 거래 단위 미만: order_id={self.order_id}, "
                    f"amount={amount}, min_trade_amount={self.min_trade_amount}"
                )
                raise ValueError(
                    f"Fill amount {amount} is below minimum trade amount {self.min_trade_amount}"
                )

    def __str__(self) -> str:
        return (
            f"SpotOrder(id={self.order_id}, side={self.side.name}, "
            f"type={self.order_type}, price={self.price}, "
            f"amount={self.amount}, filled={self.filled_amount}, "
            f"status={self.status.value})"
        )

    def __repr__(self) -> str:
        """SpotOrder 문자열 표현."""
        return (
            f"SpotOrder(order_id={self.order_id!r}, "
            f"stock_address={self.stock_address!r}, "
            f"side={self.side!r}, order_type={self.order_type!r}, "
            f"price={self.price}, amount={self.amount}, "
            f"timestamp={self.timestamp}, stop_price={self.stop_price}, "
            f"min_trade_amount={self.min_trade_amount}, "
            f"time_in_force={self.time_in_force}, "
            f"expire_timestamp={self.expire_timestamp})"
        )
