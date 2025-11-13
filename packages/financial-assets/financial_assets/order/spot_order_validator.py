"""SpotOrder 필드 유효성 검증기."""

from __future__ import annotations
from typing import TYPE_CHECKING
from simple_logger import logger

if TYPE_CHECKING:
    from .spot_order import SpotOrder

from ..constants import OrderType, TimeInForce


class SpotOrderValidator:
    """주문 생성 시 필드 값의 유효성을 검증."""

    @staticmethod
    def validate(order: SpotOrder) -> None:
        """주문 필드 유효성 검증."""
        SpotOrderValidator._validate_basic_fields(order)
        SpotOrderValidator._validate_order_type_fields(order)
        SpotOrderValidator._validate_time_in_force_fields(order)

    @staticmethod
    def _validate_basic_fields(order: SpotOrder) -> None:
        """기본 필드 검증 (amount, timestamp, filled_amount, fee_rate, min_trade_amount)."""
        # amount 검증
        if order.amount <= 0:
            logger.error(f"주문 수량이 0 이하: order_id={order.order_id}, amount={order.amount}")
            raise ValueError(f"주문 수량은 양수여야 합니다: {order.amount}")

        # timestamp 검증
        if order.timestamp <= 0:
            logger.error(
                f"타임스탬프가 0 이하: order_id={order.order_id}, timestamp={order.timestamp}"
            )
            raise ValueError(f"타임스탬프는 양수여야 합니다: {order.timestamp}")

        # filled_amount 검증
        if order.filled_amount < 0:
            logger.error(
                f"체결 수량이 음수: order_id={order.order_id}, filled_amount={order.filled_amount}"
            )
            raise ValueError(f"체결 수량은 음수일 수 없습니다: {order.filled_amount}")

        if order.filled_amount > order.amount:
            logger.error(
                f"체결 수량이 주문 수량 초과: order_id={order.order_id}, "
                f"filled_amount={order.filled_amount}, amount={order.amount}"
            )
            raise ValueError(
                f"체결 수량({order.filled_amount})이 주문 수량({order.amount})을 초과할 수 없습니다"
            )

        # fee_rate 검증
        if order.fee_rate < 0:
            logger.error(
                f"수수료율이 음수: order_id={order.order_id}, fee_rate={order.fee_rate}"
            )
            raise ValueError(f"수수료율은 음수일 수 없습니다: {order.fee_rate}")

        # min_trade_amount 검증
        if order.min_trade_amount is not None:
            if order.min_trade_amount <= 0:
                logger.error(
                    f"최소 거래량이 0 이하: order_id={order.order_id}, "
                    f"min_trade_amount={order.min_trade_amount}"
                )
                raise ValueError(f"최소 거래량은 양수여야 합니다: {order.min_trade_amount}")

            if order.min_trade_amount > order.amount:
                logger.error(
                    f"최소 거래량이 주문 수량 초과: order_id={order.order_id}, "
                    f"min_trade_amount={order.min_trade_amount}, amount={order.amount}"
                )
                raise ValueError(
                    f"최소 거래량({order.min_trade_amount})이 "
                    f"주문 수량({order.amount})을 초과할 수 없습니다"
                )

    @staticmethod
    def _validate_order_type_fields(order: SpotOrder) -> None:
        """OrderType별 필드 검증 (LIMIT, MARKET, STOP_LIMIT, STOP_MARKET)."""
        if order.order_type == OrderType.LIMIT:
            if order.price is None:
                logger.error(f"LIMIT 주문에 가격 누락: order_id={order.order_id}")
                raise ValueError("LIMIT 주문은 가격이 필수입니다")
            if order.price <= 0:
                logger.error(
                    f"LIMIT 주문 가격이 0 이하: order_id={order.order_id}, price={order.price}"
                )
                raise ValueError(f"LIMIT 주문 가격은 양수여야 합니다: {order.price}")

        elif order.order_type == OrderType.MARKET:
            if order.price is not None:
                logger.warning(
                    f"MARKET 주문에 가격 무시됨: order_id={order.order_id}, price={order.price}"
                )

        elif order.order_type == OrderType.STOP_LIMIT:
            if order.price is None:
                logger.error(f"STOP_LIMIT 주문에 가격 누락: order_id={order.order_id}")
                raise ValueError("STOP_LIMIT 주문은 가격이 필수입니다")
            if order.price <= 0:
                logger.error(
                    f"STOP_LIMIT 주문 가격이 0 이하: order_id={order.order_id}, "
                    f"price={order.price}"
                )
                raise ValueError(f"STOP_LIMIT 주문 가격은 양수여야 합니다: {order.price}")

            if order.stop_price is None:
                logger.error(f"STOP_LIMIT 주문에 stop_price 누락: order_id={order.order_id}")
                raise ValueError("STOP_LIMIT 주문은 stop_price가 필수입니다")
            if order.stop_price <= 0:
                logger.error(
                    f"STOP_LIMIT 주문 stop_price가 0 이하: order_id={order.order_id}, "
                    f"stop_price={order.stop_price}"
                )
                raise ValueError(
                    f"STOP_LIMIT 주문 stop_price는 양수여야 합니다: {order.stop_price}"
                )

        elif order.order_type == OrderType.STOP_MARKET:
            if order.stop_price is None:
                logger.error(f"STOP_MARKET 주문에 stop_price 누락: order_id={order.order_id}")
                raise ValueError("STOP_MARKET 주문은 stop_price가 필수입니다")
            if order.stop_price <= 0:
                logger.error(
                    f"STOP_MARKET 주문 stop_price가 0 이하: order_id={order.order_id}, "
                    f"stop_price={order.stop_price}"
                )
                raise ValueError(
                    f"STOP_MARKET 주문 stop_price는 양수여야 합니다: {order.stop_price}"
                )

    @staticmethod
    def _validate_time_in_force_fields(order: SpotOrder) -> None:
        """TimeInForce별 필드 검증 (GTD)."""
        if order.time_in_force == TimeInForce.GTD:
            if order.expire_timestamp is None:
                logger.error(f"GTD 주문에 expire_timestamp 누락: order_id={order.order_id}")
                raise ValueError("GTD 주문은 expire_timestamp가 필수입니다")

            if order.expire_timestamp <= order.timestamp:
                logger.error(
                    f"GTD 주문의 expire_timestamp가 timestamp 이하: order_id={order.order_id}, "
                    f"expire_timestamp={order.expire_timestamp}, timestamp={order.timestamp}"
                )
                raise ValueError(
                    f"만료 시각({order.expire_timestamp})은 "
                    f"주문 시각({order.timestamp})보다 커야 합니다"
                )
