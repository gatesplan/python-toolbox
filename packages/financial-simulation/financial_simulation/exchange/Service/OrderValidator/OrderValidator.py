"""주문 실행 전 거래소 컨텍스트 검증."""

from __future__ import annotations

from simple_logger import func_logging, logger
from financial_assets.order import SpotOrder
from financial_assets.constants import OrderSide, OrderType
from ...Core.Portfolio import Portfolio
from ...Core.MarketData import MarketData


class OrderValidator:
    """주문 실행 전 거래소 컨텍스트 검증 (잔고/자산 충분성)."""

    def __init__(self, portfolio: Portfolio, market_data: MarketData):
        """OrderValidator 초기화."""
        self._portfolio = portfolio
        self._market_data = market_data

    def validate_order(self, order: SpotOrder) -> None:
        """주문 실행 전 거래소 컨텍스트 검증."""
        if order.side == OrderSide.BUY:
            self._validate_buy_order(order)
        elif order.side == OrderSide.SELL:
            self._validate_sell_order(order)

    @func_logging(level="INFO")
    def _validate_buy_order(self, order: SpotOrder) -> None:
        """BUY 주문 잔고 검증."""
        quote_symbol = order.stock_address.quote

        # 가격 결정 (LIMIT/MARKET)
        if order.order_type == OrderType.MARKET:
            # MARKET 주문: 현재 시장가 조회
            symbol = order.stock_address.to_symbol()
            symbol_str = symbol.to_slash()
            current_price_data = self._market_data.get_current(symbol_str)
            if current_price_data is None:
                logger.error(
                    f"MARKET 주문 검증 실패: 현재 시장가 조회 불가 - order_id={order.order_id}, symbol={symbol_str}"
                )
                raise ValueError(f"MARKET 주문 검증 실패: 현재 시장가 조회 불가 (symbol={symbol_str})")
            price = current_price_data.c  # close price 사용
        else:
            # LIMIT/STOP_LIMIT: 주문 가격 사용
            price = order.price

        # 필요 자금 계산
        required = price * order.amount
        available = self._portfolio.get_available_balance(quote_symbol)

        if available < required:
            logger.error(
                f"BUY 주문 잔고 부족: order_id={order.order_id}, "
                f"quote={quote_symbol}, available={available}, required={required}"
            )
            raise ValueError(
                f"잔고 부족: available={available} {quote_symbol}, required={required} {quote_symbol}"
            )

        logger.info(
            f"BUY 주문 검증 성공: order_id={order.order_id}, "
            f"quote={quote_symbol}, available={available}, required={required}"
        )

    @func_logging(level="INFO")
    def _validate_sell_order(self, order: SpotOrder) -> None:
        """SELL 주문 자산 보유량 검증."""
        symbol = order.stock_address.to_symbol()
        ticker = symbol.to_dash()

        # 필요 자산 (Position 확인)
        required = order.amount
        available = self._portfolio.get_available_position(symbol)

        if available < required:
            logger.error(
                f"SELL 주문 자산 부족: order_id={order.order_id}, "
                f"ticker={ticker}, available={available}, required={required}"
            )
            raise ValueError(
                f"자산 부족: available={available} {ticker}, required={required} {ticker}"
            )

        logger.info(
            f"SELL 주문 검증 성공: order_id={order.order_id}, "
            f"ticker={ticker}, available={available}, required={required}"
        )
