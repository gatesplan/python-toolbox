"""SpotExchange API Layer"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
    from financial_simulation.tradesim.API.TradeSimulation import TradeSimulation

from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_simulation.exchange.Core.Portfolio.Portfolio import Portfolio
from financial_simulation.exchange.Core.OrderBook.OrderBook import OrderBook
from financial_simulation.exchange.Service.OrderValidator.OrderValidator import OrderValidator
from financial_simulation.exchange.Service.OrderExecutor.OrderExecutor import OrderExecutor
from financial_simulation.exchange.Service.PositionManager.PositionManager import PositionManager


class SpotExchange:
    """Spot 거래소 API Layer. 외부 진입점으로 주문, 잔고, 포지션 관리 기능 제공."""

    def __init__(
        self,
        initial_balance: float,
        market_data: MarketData,
        trade_simulation: TradeSimulation,
        quote_currency: str = "USDT"
    ):
        """SpotExchange 초기화.

        Args:
            initial_balance: 초기 자산 (quote_currency 기준)
            market_data: MarketData 인스턴스
            trade_simulation: TradeSimulation 인스턴스
            quote_currency: 기준 화폐
        """
        # Core 컴포넌트 생성
        self._portfolio = Portfolio()
        self._orderbook = OrderBook()
        self._market_data = market_data

        # 초기 자금 입금
        self._initial_balance = initial_balance
        self._quote_currency = quote_currency
        self._portfolio.deposit_currency(quote_currency, initial_balance)

        # Service 컴포넌트 생성
        self._order_validator = OrderValidator(self._portfolio, self._market_data)
        self._order_executor = OrderExecutor(
            self._portfolio,
            self._orderbook,
            self._market_data,
            trade_simulation
        )
        self._position_manager = PositionManager(
            self._portfolio,
            self._market_data,
            initial_balance
        )

        # 거래 내역
        self._trade_history: list[SpotTrade] = []

    def place_order(self, order: SpotOrder) -> list[SpotTrade]:
        """주문 실행.

        Args:
            order: 완성된 SpotOrder 객체

        Returns:
            list[SpotTrade]: 체결된 Trade 리스트

        Raises:
            ValueError: 잔고/자산 부족 시
        """
        # 1. 주문 검증 (거래소 컨텍스트)
        self._order_validator.validate_order(order)

        # 2. 주문 실행
        trades = self._order_executor.execute_order(order)

        # 3. 거래 내역 추가
        self._trade_history.extend(trades)

        return trades

    def cancel_order(self, order_id: str) -> None:
        """미체결 주문 취소.

        Args:
            order_id: 주문 ID

        Raises:
            KeyError: 주문이 존재하지 않을 때
        """
        self._order_executor.cancel_order(order_id)

    def get_open_orders(self, symbol: str | None = None) -> list[SpotOrder]:
        """미체결 주문 조회.

        Args:
            symbol: 필터링할 심볼 (None이면 전체)

        Returns:
            list[SpotOrder]: 미체결 주문 리스트
        """
        if symbol is None:
            return self._orderbook.get_all_orders()
        else:
            return self._orderbook.get_orders_by_symbol(symbol)

    def get_trade_history(self, symbol: str | None = None) -> list[SpotTrade]:
        """거래 내역 조회.

        Args:
            symbol: 필터링할 심볼 (None이면 전체)

        Returns:
            list[SpotTrade]: 거래 내역 리스트
        """
        if symbol is None:
            return self._trade_history
        else:
            # symbol로 필터링
            return [
                trade for trade in self._trade_history
                if f"{trade.order.stock_address.base}/{trade.order.stock_address.quote}" == symbol
            ]

    def get_balance(self, currency: str | None = None) -> float | dict[str, float]:
        """Currency 잔고 조회.

        Args:
            currency: 화폐 심볼 (None이면 전체)

        Returns:
            float | dict[str, float]: 단일 화폐는 float, 전체는 dict
        """
        if currency is None:
            # 전체 잔고 조회
            currencies = self._portfolio.get_currencies()
            return {curr: self._portfolio.get_available_balance(curr) for curr in currencies}
        else:
            return self._portfolio.get_available_balance(currency)

    def get_positions(self) -> dict[str, float]:
        """보유 포지션 조회.

        Returns:
            dict[str, float]: {ticker: amount}
        """
        return self._position_manager.get_positions()

    def get_position_value(self, ticker: str) -> dict[str, float]:
        """특정 포지션의 상세 가치 정보.

        Args:
            ticker: Position ticker

        Returns:
            dict: 포지션 가치 정보
        """
        return {
            "book_value": self._position_manager.get_position_book_value(ticker),
            "market_value": self._position_manager.get_position_market_value(ticker),
            "pnl": self._position_manager.get_position_pnl(ticker),
            "pnl_ratio": self._position_manager.get_position_pnl_ratio(ticker)
        }

    def get_total_value(self) -> float:
        """총 자산 가치.

        Returns:
            float: 총 자산 가치 (quote_currency 기준)
        """
        return self._position_manager.get_total_value(quote_currency=self._quote_currency)

    def get_statistics(self) -> dict[str, float]:
        """포트폴리오 통계 조회.

        Returns:
            dict: 통계 정보
        """
        return {
            "total_value": self._position_manager.get_total_value(quote_currency=self._quote_currency),
            "total_pnl": self._position_manager.get_total_pnl(),
            "total_pnl_ratio": self._position_manager.get_total_pnl_ratio(),
            "currency_value": self._position_manager.get_currency_value(quote_currency=self._quote_currency),
            "position_value": sum(
                self._position_manager.get_position_market_value(ticker)
                for ticker in self._position_manager.get_positions().keys()
            ),
            "allocation": self._position_manager.get_position_allocation()
        }

    def step(self) -> bool:
        """다음 시장 틱으로 이동.

        Returns:
            bool: 계속 진행 가능하면 True, 종료면 False
        """
        # 1. MarketData 커서 이동
        can_continue = self._market_data.step()

        if not can_continue:
            return False

        # 2. GTD 주문 만료 처리
        symbols = self._market_data.get_symbols()
        if symbols:
            current_timestamp = self._market_data.get_current_timestamp(symbols[0])
            if current_timestamp is not None:
                expired_order_ids = self._orderbook.expire_orders(current_timestamp)

                # 3. 만료된 주문의 자산 잠금 해제
                for order_id in expired_order_ids:
                    try:
                        self._portfolio.unlock_currency(order_id)
                    except KeyError:
                        # 이미 해제된 경우 무시
                        pass

        return True

    def reset(self) -> None:
        """거래소 초기화."""
        # 1. Portfolio 초기화 (새로 생성)
        self._portfolio = Portfolio()
        self._portfolio.deposit_currency(self._quote_currency, self._initial_balance)

        # 2. OrderBook 초기화 (새로 생성)
        self._orderbook = OrderBook()

        # 3. MarketData 커서 리셋
        self._market_data.reset()

        # 4. Service 컴포넌트 재생성 (Portfolio 참조 갱신)
        self._order_validator = OrderValidator(self._portfolio, self._market_data)
        self._order_executor = OrderExecutor(
            self._portfolio,
            self._orderbook,
            self._market_data,
            self._order_executor._trade_simulation  # TradeSimulation 재사용
        )
        self._position_manager = PositionManager(
            self._portfolio,
            self._market_data,
            self._initial_balance
        )

        # 5. 거래 내역 초기화
        self._trade_history = []

    def get_current_timestamp(self) -> int | None:
        """현재 시장 타임스탬프 조회.

        Returns:
            int | None: 타임스탬프
        """
        # MarketData에서 첫 번째 심볼의 현재 타임스탬프 조회
        symbols = self._market_data.get_symbols()
        if not symbols:
            return None
        return self._market_data.get_current_timestamp(symbols[0])

    def get_current_price(self, symbol: str) -> float | None:
        """현재 시장 가격 조회.

        Args:
            symbol: 심볼 (예: "BTC/USDT")

        Returns:
            float | None: 현재 종가
        """
        price_data = self._market_data.get_current(symbol)
        if price_data is None:
            return None
        return price_data.c

    def is_finished(self) -> bool:
        """시뮬레이션 종료 여부.

        Returns:
            bool: 종료 여부
        """
        return self._market_data.is_finished()
