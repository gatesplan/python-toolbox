"""Spot order data structure.

This module provides the SpotOrder class for representing pending spot trade orders
and managing fill status. Spot orders involve immediate asset exchange.
"""

from __future__ import annotations
from typing import Optional
from ..trade import SpotTrade, SpotSide
from ..stock_address import StockAddress
from ..token import Token
from ..pair import Pair
from simple_logger import init_logging, logger


class SpotOrder:
    """
    미체결 또는 부분 체결된 현물 거래 주문을 표현하는 가변 데이터 구조.

    SpotOrder는 현물 거래 시뮬레이션이나 실제 거래소 API에서 발생한 주문 정보를
    추적하며, 부분/전체 체결 시 SpotTrade 객체를 생성하는 팩토리 역할을 합니다.
    SpotTrade와 달리 SpotOrder는 체결에 따라 상태가 변경되는 가변 객체입니다.

    현물 주문은 자산의 즉시 교환을 의미하며, 레버리지나 포지션 개념이 없습니다.
    선물 주문은 FuturesOrder를 사용하세요.

    Attributes:
        order_id (str): 주문 식별자
        stock_address (StockAddress): 거래가 발생하는 시장/거래소 정보
        side (SpotSide): 거래 방향 (BUY, SELL)
        order_type (str): 주문 타입 ("market", "limit", "stop")
        price (float | None): 지정가 (시장가는 None)
        amount (float): 주문 총 수량 (asset 기준)
        filled_amount (float): 체결된 누적 수량
        status (str): 주문 상태 ("pending", "partial", "filled", "canceled")
        timestamp (int): 주문 생성 시각 (Unix timestamp)
        stop_price (float | None): stop order 발동 가격 (옵션)

    Examples:
        >>> from financial_assets.order import SpotOrder
        >>> from financial_assets.trade import SpotSide
        >>> from financial_assets.stock_address import StockAddress
        >>>
        >>> stock_address = StockAddress(
        ...     archetype="crypto",
        ...     exchange="binance",
        ...     tradetype="spot",
        ...     base="btc",
        ...     quote="usdt",
        ...     timeframe="1d"
        ... )
        >>>
        >>> # Limit order 생성
        >>> order = SpotOrder(
        ...     order_id="order-123",
        ...     stock_address=stock_address,
        ...     side=SpotSide.BUY,
        ...     order_type="limit",
        ...     price=50000.0,
        ...     amount=1.0,
        ...     timestamp=1234567890
        ... )
        >>>
        >>> # 부분 체결
        >>> trade = order.fill_by_asset_amount(0.3, 50100.0, 1234567900)
        >>> order.filled_amount
        0.3
        >>> order.status
        'partial'
        >>> order.remaining_asset()
        0.7
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
    ):
        """
        SpotOrder 초기화.

        Args:
            order_id: 주문 식별자
            stock_address: 거래 시장 정보
            side: 거래 방향 (BUY, SELL)
            order_type: 주문 타입 ("market", "limit", "stop")
            price: 지정가 (시장가는 None)
            amount: 주문 총 수량
            timestamp: 주문 생성 시각
            stop_price: stop order 발동 가격 (선택적)
        """
        self.order_id = order_id
        self.stock_address = stock_address
        self.side = side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.filled_amount = 0.0
        self.status = "pending"
        self.timestamp = timestamp
        self.stop_price = stop_price

    def fill_by_asset_amount(
        self, amount: float, price: float, timestamp: int
    ) -> SpotTrade:
        """
        자산 수량 기준으로 주문을 체결하고 SpotTrade 객체를 생성합니다.

        Args:
            amount: 체결할 자산 수량
            price: 체결 가격
            timestamp: 체결 시각

        Returns:
            SpotTrade: 생성된 거래 객체

        Raises:
            ValueError: 체결 수량이 음수이거나 미체결 수량을 초과할 때
            ValueError: 주문이 이미 취소된 경우

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-1",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=1.0,
            ...     timestamp=1234567890
            ... )
            >>> trade = order.fill_by_asset_amount(0.3, 50100.0, 1234567900)
            >>> trade.pair.get_asset()
            0.3
            >>> trade.pair.get_value()
            15030.0
        """
        logger.info(f"주문 체결 시작: order_id={self.order_id}, fill_amount={amount}, price={price}")

        self._validate_fill(amount)

        # 체결 수량 업데이트
        self.filled_amount += amount

        # 상태 업데이트
        if self.filled_amount >= self.amount:
            self.status = "filled"
            logger.info(f"주문 완전 체결: order_id={self.order_id}, filled={self.filled_amount}/{self.amount}")
        else:
            self.status = "partial"
            logger.info(f"주문 부분 체결: order_id={self.order_id}, filled={self.filled_amount}/{self.amount}")

        # SpotTrade 객체 생성
        asset_token = Token(self.stock_address.base, amount)
        value_token = Token(self.stock_address.quote, amount * price)
        pair = Pair(asset=asset_token, value=value_token)

        return SpotTrade(
            stock_address=self.stock_address,
            trade_id=self.order_id,
            fill_id=f"fill-{timestamp}",
            side=self.side,
            pair=pair,
            timestamp=timestamp,
        )

    def fill_by_value_amount(
        self, amount: float, price: float, timestamp: int
    ) -> SpotTrade:
        """
        가치 수량 기준으로 주문을 체결하고 SpotTrade 객체를 생성합니다.

        Args:
            amount: 체결할 가치 수량 (quote currency)
            price: 체결 가격
            timestamp: 체결 시각

        Returns:
            SpotTrade: 생성된 거래 객체

        Raises:
            ValueError: 체결 수량이 음수이거나 미체결 수량을 초과할 때
            ValueError: 주문이 이미 취소된 경우
            ValueError: price가 0일 때

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-2",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=1.0,
            ...     timestamp=1234567890
            ... )
            >>> trade = order.fill_by_value_amount(15000.0, 50000.0, 1234567900)
            >>> trade.pair.get_asset()
            0.3
            >>> trade.pair.get_value()
            15000.0
        """
        if price == 0:
            raise ValueError("Price cannot be zero for value-based fill")

        # value amount를 asset amount로 변환
        asset_amount = amount / price
        return self.fill_by_asset_amount(asset_amount, price, timestamp)

    def remaining_asset(self) -> float:
        """
        미체결 자산 수량을 반환합니다.

        Returns:
            float: 남은 자산 수량

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-3",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=2.0,
            ...     timestamp=1234567890
            ... )
            >>> order.remaining_asset()
            2.0
            >>> order.fill_by_asset_amount(0.7, 50000.0, 1234567900)
            >>> order.remaining_asset()
            1.3
        """
        return self.amount - self.filled_amount

    def remaining_value(self) -> float:
        """
        미체결 가치 수량을 반환합니다.

        지정가 주문의 경우 price 기준으로 계산됩니다.

        Returns:
            float: 남은 가치 수량

        Raises:
            ValueError: 시장가 주문(price=None)에서 호출 시

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-4",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=1.0,
            ...     timestamp=1234567890
            ... )
            >>> order.remaining_value()
            50000.0
            >>> order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
            >>> order.remaining_value()
            35000.0
        """
        if self.price is None:
            raise ValueError("Cannot calculate remaining_value for market orders")
        return self.remaining_asset() * self.price

    def remaining_rate(self) -> float:
        """
        미체결 비율을 반환합니다.

        Returns:
            float: 미체결 비율 (0.0 ~ 1.0)

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-5",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=1.0,
            ...     timestamp=1234567890
            ... )
            >>> order.remaining_rate()
            1.0
            >>> order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
            >>> order.remaining_rate()
            0.7
        """
        if self.amount == 0:
            return 0.0
        return self.remaining_asset() / self.amount

    def is_filled(self) -> bool:
        """
        주문이 완전히 체결되었는지 확인합니다.

        Returns:
            bool: 완전 체결 여부

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-6",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=1.0,
            ...     timestamp=1234567890
            ... )
            >>> order.is_filled()
            False
            >>> order.fill_by_asset_amount(1.0, 50000.0, 1234567900)
            >>> order.is_filled()
            True
        """
        return self.status == "filled"

    def cancel(self) -> None:
        """
        주문을 취소합니다.

        취소된 주문은 더 이상 체결할 수 없습니다.

        Examples:
            >>> order = SpotOrder(
            ...     order_id="order-7",
            ...     stock_address=stock_address,
            ...     side=SpotSide.BUY,
            ...     order_type="limit",
            ...     price=50000.0,
            ...     amount=1.0,
            ...     timestamp=1234567890
            ... )
            >>> order.cancel()
            >>> order.status
            'canceled'
        """
        logger.info(f"주문 취소: order_id={self.order_id}, filled={self.filled_amount}/{self.amount}")
        self.status = "canceled"

    def _validate_fill(self, amount: float) -> None:
        """
        체결 요청을 검증합니다.

        Args:
            amount: 체결 요청 수량

        Raises:
            ValueError: 체결 수량이 음수이거나 미체결 수량을 초과할 때
            ValueError: 주문이 이미 취소된 경우
        """
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

    def __str__(self) -> str:
        """
        SpotOrder의 읽기 쉬운 문자열 표현을 반환합니다.

        Returns:
            str: 주문 ID, 방향, 타입, 수량 정보를 포함한 문자열
        """
        return (
            f"SpotOrder(id={self.order_id}, side={self.side.name}, "
            f"type={self.order_type}, price={self.price}, "
            f"amount={self.amount}, filled={self.filled_amount}, "
            f"status={self.status})"
        )

    def __repr__(self) -> str:
        """
        SpotOrder의 상세한 문자열 표현을 반환합니다.

        Returns:
            str: 모든 필드 정보를 포함한 재생성 가능한 형식의 문자열
        """
        return (
            f"SpotOrder(order_id={self.order_id!r}, "
            f"stock_address={self.stock_address!r}, "
            f"side={self.side!r}, order_type={self.order_type!r}, "
            f"price={self.price}, amount={self.amount}, "
            f"timestamp={self.timestamp}, stop_price={self.stop_price})"
        )
