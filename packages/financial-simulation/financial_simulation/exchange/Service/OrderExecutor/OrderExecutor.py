"""주문 실행 및 체결 처리."""

from __future__ import annotations
from typing import TYPE_CHECKING
from simple_logger import func_logging, logger
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.pair import Pair
from financial_assets.token import Token

if TYPE_CHECKING:
    from ...Core.Portfolio import Portfolio
    from ...Core.OrderBook import OrderBook
    from ...Core.MarketData import MarketData
    from financial_simulation.tradesim.API.TradeSimulation import TradeSimulation

from financial_assets.constants import OrderSide, OrderType, TimeInForce


class OrderExecutor:
    """주문 실행 및 체결 처리."""

    def __init__(
        self,
        portfolio: Portfolio,
        orderbook: OrderBook,
        market_data: MarketData,
        trade_simulation: TradeSimulation,
    ):
        """OrderExecutor 초기화."""
        self._portfolio = portfolio
        self._orderbook = orderbook
        self._market_data = market_data
        self._trade_simulation = trade_simulation

    @func_logging(level="INFO")
    def execute_order(self, order: SpotOrder) -> list[SpotTrade]:
        """주문 실행 및 체결 처리."""
        # 1. 현재 Price 조회
        symbol = order.stock_address.to_symbol()
        current_price = self._market_data.get_current(symbol)
        if current_price is None:
            logger.error(f"주문 실행 실패: 현재 시장가 조회 불가 - order_id={order.order_id}, symbol={symbol.to_slash()}")
            raise ValueError(f"주문 실행 실패: 현재 시장가 조회 불가 (symbol={symbol.to_slash()})")

        # 2. TradeSimulation에 위임
        trades = self._trade_simulation.process(order, current_price)

        # 3. 체결된 Trade들을 Portfolio에 반영
        filled_amount = 0.0
        for trade in trades:
            self._portfolio.process_trade(trade)
            filled_amount += trade.pair.get_asset()

        # 4. 미체결 수량 계산
        unfilled_amount = order.amount - filled_amount

        # 5. MARKET 주문은 항상 IOC로 처리 (미체결 즉시 취소)
        if order.order_type == OrderType.MARKET:
            logger.info(
                f"MARKET 주문 처리 완료: order_id={order.order_id}, "
                f"filled={filled_amount}, unfilled={unfilled_amount} (즉시 취소)"
            )
            return trades

        # 6. TimeInForce 처리 (LIMIT 주문만)
        if order.time_in_force == TimeInForce.FOK:
            # FOK: 완전 체결 아니면 실패
            if unfilled_amount > 0:
                # Portfolio 롤백 (체결된 Trade들을 역으로 처리)
                self._rollback_trades(trades)
                logger.error(
                    f"FOK 주문 실패: 부분 체결 - order_id={order.order_id}, "
                    f"amount={order.amount}, filled={filled_amount}"
                )
                raise ValueError(f"FOK 주문 실패: 부분 체결 (filled={filled_amount}/{order.amount})")
            logger.info(f"FOK 주문 완전 체결 성공: order_id={order.order_id}, amount={filled_amount}")
            return trades

        elif order.time_in_force == TimeInForce.IOC:
            # IOC: 부분 체결만 처리, 미체결 즉시 취소
            logger.info(
                f"IOC 주문 처리 완료: order_id={order.order_id}, "
                f"filled={filled_amount}, unfilled={unfilled_amount} (즉시 취소)"
            )
            return trades

        else:
            # GTC/GTD: 미체결 수량 있으면 OrderBook 추가 및 자산 잠금
            if unfilled_amount > 0:
                self._orderbook.add_order(order)
                self._lock_assets(order, unfilled_amount)
                logger.info(
                    f"주문 부분 체결 후 OrderBook 추가: order_id={order.order_id}, "
                    f"filled={filled_amount}, unfilled={unfilled_amount}"
                )
            else:
                logger.info(f"주문 완전 체결: order_id={order.order_id}, amount={filled_amount}")

            return trades

    @func_logging(level="INFO")
    def cancel_order(self, order_id: str) -> None:
        """미체결 주문 취소."""
        # OrderBook에서 주문 조회
        order = self._orderbook.get_order(order_id)
        if order is None:
            logger.error(f"주문 취소 실패: 주문을 찾을 수 없음 - order_id={order_id}")
            raise KeyError(f"주문을 찾을 수 없음: order_id={order_id}")

        # OrderBook에서 제거
        self._orderbook.remove_order(order_id)

        # 잠긴 자산 해제
        self._portfolio.unlock_currency(order_id)

        logger.info(f"주문 취소 완료: order_id={order_id}")

    @func_logging(level="INFO")
    def _rollback_trades(self, trades: list[SpotTrade]) -> None:
        """체결된 Trade들을 역으로 처리 (FOK 실패 시 롤백)."""
        for trade in trades:
            # Trade를 역으로 적용 (BUY <-> SELL 반대)
            # 원래 trade의 order를 복사하여 side만 반대로
            reversed_order = SpotOrder(
                order_id=f"rollback_{trade.order.order_id}",
                stock_address=trade.order.stock_address,
                side=OrderSide.SELL if trade.order.side == OrderSide.BUY else OrderSide.BUY,
                order_type=trade.order.order_type,
                price=trade.order.price,
                amount=trade.pair.get_asset(),
                timestamp=trade.timestamp,
            )

            # Trade의 Pair도 그대로 사용 (역으로 적용하면 같은 효과)
            reversed_trade = SpotTrade(
                trade_id=f"rollback_{trade.trade_id}",
                order=reversed_order,
                pair=trade.pair,
                timestamp=trade.timestamp,
                fee=None,  # 롤백 시 수수료 무시
            )
            self._portfolio.process_trade(reversed_trade)

    @func_logging(level="INFO")
    def _lock_assets(self, order: SpotOrder, amount: float) -> None:
        """미체결 수량에 대한 자산 잠금."""
        if order.side == OrderSide.BUY:
            # BUY: quote 화폐 잠금
            quote_symbol = order.stock_address.quote
            required = order.price * amount
            self._portfolio.lock_currency(order.order_id, quote_symbol, required)
            logger.info(
                f"BUY 주문 자산 잠금: order_id={order.order_id}, "
                f"quote={quote_symbol}, amount={required}"
            )
        elif order.side == OrderSide.SELL:
            # SELL: base Position 잠금
            symbol = order.stock_address.to_symbol()
            self._portfolio.lock_position(order.order_id, symbol, amount)
            logger.info(
                f"SELL 주문 자산 잠금: order_id={order.order_id}, "
                f"ticker={symbol.to_dash()}, amount={amount}"
            )
