from __future__ import annotations
from typing import Optional
from ..trade import SpotSide
from ..stock_address import StockAddress
from simple_logger import init_logging, logger


class SpotOrder:
    """Represents a spot trading order with immutable update pattern.

    SpotOrder encapsulates all information needed for stateless trade processing,
    including order details, fill state, fees, and minimum trade constraints.
    All state modifications return new instances, preserving immutability.

    Attributes:
        order_id: Unique identifier for the order
        stock_address: Market information (exchange, trading pair, etc.)
        side: BUY or SELL
        order_type: "limit", "market", or "stop"
        price: Limit price (None for market orders)
        amount: Total order amount in base currency
        timestamp: Order creation time
        stop_price: Stop price for stop orders (optional)
        filled_amount: Amount already filled (default: 0.0)
        status: Order status - "pending", "partial", "filled", or "canceled"
        fee_rate: Trading fee rate (default: 0.0)
        min_trade_amount: Minimum trade unit for partial fills (optional)
            When set, enforces realistic exchange constraints in simulations.
            Final fills are allowed even if below minimum.

    Example:
        >>> order = SpotOrder(
        ...     order_id="order-1",
        ...     stock_address=stock_address,
        ...     side=SpotSide.BUY,
        ...     order_type="limit",
        ...     price=50000.0,
        ...     amount=1.0,
        ...     timestamp=1234567890,
        ...     min_trade_amount=0.001  # Min 0.001 BTC per fill
        ... )
        >>> filled = order.fill_by_asset_amount(0.5)  # OK: above minimum
        >>> filled.is_remaining_below_min()  # Check if remainder is too small
        False
    """

    @init_logging(level="INFO", log_params=True)
    def __init__(
        self,
        order_id: str,
        stock_address: StockAddress,
        side: SpotSide,
        order_type: str,
        price: Optional[float],
        amount: float,
        timestamp: int,
        stop_price: Optional[float] = None,
        filled_amount: float = 0.0,
        status: str = "pending",
        fee_rate: float = 0.0,
        min_trade_amount: Optional[float] = None,
    ):
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

    def _clone(self, **overrides) -> SpotOrder:
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
        )

    def fill_by_asset_amount(self, amount: float) -> SpotOrder:
        logger.info(f"주문 체결 시작: order_id={self.order_id}, fill_amount={amount}")
        self._validate_fill(amount)

        new_filled = self.filled_amount + amount

        if new_filled >= self.amount:
            new_status = "filled"
            logger.info(f"주문 완전 체결: order_id={self.order_id}, filled={new_filled}/{self.amount}")
        elif new_filled > 0:
            new_status = "partial"
            logger.info(f"주문 부분 체결: order_id={self.order_id}, filled={new_filled}/{self.amount}")
        else:
            new_status = "pending"

        return self._clone(filled_amount=new_filled, status=new_status)

    def fill_by_value_amount(self, amount: float) -> SpotOrder:
        if self.price is None:
            raise ValueError("Cannot use fill_by_value_amount for market orders (price=None)")
        if self.price == 0:
            raise ValueError("Price cannot be zero for value-based fill")

        asset_amount = amount / self.price
        return self.fill_by_asset_amount(asset_amount)

    def remaining_asset(self) -> float:
        return self.amount - self.filled_amount

    def remaining_value(self) -> float:
        if self.price is None:
            raise ValueError("Cannot calculate remaining_value for market orders")
        return self.remaining_asset() * self.price

    def remaining_rate(self) -> float:
        if self.amount == 0:
            return 0.0
        return self.remaining_asset() / self.amount

    def is_filled(self) -> bool:
        return self.status == "filled"

    def to_pending_state(self) -> SpotOrder:
        return self._clone(status="pending")

    def to_partial_state(self) -> SpotOrder:
        return self._clone(status="partial")

    def to_filled_state(self) -> SpotOrder:
        return self._clone(status="filled")

    def to_canceled_state(self) -> SpotOrder:
        logger.info(f"주문 취소: order_id={self.order_id}, filled={self.filled_amount}/{self.amount}")
        return self._clone(status="canceled")

    def is_remaining_below_min(self) -> bool:
        """Check if remaining amount is below minimum trade amount.

        Returns:
            True if min_trade_amount is set and remaining amount is below it, False otherwise.
        """
        if self.min_trade_amount is None:
            return False
        return self.remaining_asset() < self.min_trade_amount

    def _validate_fill(self, amount: float) -> None:
        if self.status == "canceled":
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
            f"status={self.status})"
        )

    def __repr__(self) -> str:
        return (
            f"SpotOrder(order_id={self.order_id!r}, "
            f"stock_address={self.stock_address!r}, "
            f"side={self.side!r}, order_type={self.order_type!r}, "
            f"price={self.price}, amount={self.amount}, "
            f"timestamp={self.timestamp}, stop_price={self.stop_price}, "
            f"min_trade_amount={self.min_trade_amount})"
        )
