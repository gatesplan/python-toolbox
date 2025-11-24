"""SpotExchange API Layer"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from financial_simulation.exchange.Core.MarketData.MarketData import MarketData

from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.constants import OrderStatus
from financial_simulation.exchange.Core.Portfolio.Portfolio import Portfolio
from financial_simulation.exchange.Core.OrderBook.OrderBook import OrderBook
from financial_simulation.exchange.Core.OrderHistory import OrderHistory, OrderRecord
from financial_simulation.exchange.Service.OrderValidator.OrderValidator import OrderValidator
from financial_simulation.exchange.Service.OrderExecutor.OrderExecutor import OrderExecutor
from financial_simulation.exchange.Service.PositionManager.PositionManager import PositionManager
from financial_simulation.exchange.Service.MarketDataService.MarketDataService import MarketDataService
from financial_simulation.tradesim.API.TradeSimulation import TradeSimulation


class SpotExchange:
    """Spot 거래소 API Layer. 외부 진입점으로 주문, 잔고, 포지션 관리 기능 제공."""

    def __init__(
        self,
        initial_balance: float,
        market_data: MarketData,
        maker_fee_ratio: float = 0.001,
        taker_fee_ratio: float = 0.002,
        quote_currency: str = "USDT"
    ):
        """SpotExchange 초기화.

        Args:
            initial_balance: 초기 자산 (quote_currency 기준)
            market_data: MarketData 인스턴스
            maker_fee_ratio: Maker 수수료 비율 (기본값: 0.1%)
            taker_fee_ratio: Taker 수수료 비율 (기본값: 0.2%)
            quote_currency: 기준 화폐
        """
        # Core 컴포넌트 생성
        self._portfolio = Portfolio()
        self._orderbook = OrderBook()
        self._order_history = OrderHistory()
        self._market_data = market_data

        # 초기 자금 입금
        self._initial_balance = initial_balance
        self._quote_currency = quote_currency
        self._portfolio.deposit_currency(quote_currency, initial_balance)

        # 수수료 비율 저장
        self._maker_fee_ratio = maker_fee_ratio
        self._taker_fee_ratio = taker_fee_ratio

        # TradeSimulation 생성 (내부 컴포넌트)
        self._trade_simulation = TradeSimulation(
            maker_fee_ratio=maker_fee_ratio,
            taker_fee_ratio=taker_fee_ratio
        )

        # Service 컴포넌트 생성
        self._order_validator = OrderValidator(self._portfolio, self._market_data)
        self._order_executor = OrderExecutor(
            self._portfolio,
            self._orderbook,
            self._market_data,
            self._trade_simulation,
            self._order_history
        )
        self._position_manager = PositionManager(
            self._portfolio,
            self._market_data,
            initial_balance
        )
        self._market_data_service = MarketDataService(self._market_data)

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

    def get_order(self, order_id: str) -> SpotOrder | None:
        """개별 주문 조회 (미체결 + 이력).

        Args:
            order_id: 주문 ID

        Returns:
            SpotOrder | None: 주문 객체 또는 None
        """
        # 1. OrderBook에서 미체결 주문 조회
        order = self._orderbook.get_order(order_id)
        if order is not None:
            return order

        # 2. OrderHistory에서 이력 조회
        record = self._order_history.get_record(order_id)
        return record.order if record else None

    def get_order_status(self, order_id: str) -> OrderStatus | None:
        """주문 상태 조회.

        Args:
            order_id: 주문 ID

        Returns:
            OrderStatus | None: 주문 상태 또는 None
        """
        # OrderBook에 있으면 미체결 상태 확인
        order = self._orderbook.get_order(order_id)
        if order is not None:
            # OrderHistory에서 최신 상태 조회
            record = self._order_history.get_record(order_id)
            return record.status if record else OrderStatus.NEW

        # OrderHistory에서만 조회
        record = self._order_history.get_record(order_id)
        return record.status if record else None

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
                if trade.order.stock_address.to_symbol().to_slash() == symbol
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
        current_timestamp = self._market_data.get_current_timestamp()
        expired_order_ids = self._orderbook.expire_orders(current_timestamp)

        # 3. 만료된 주문의 자산 잠금 해제 및 이력 추가
        for order_id in expired_order_ids:
            try:
                self._portfolio.unlock_currency(order_id)
            except KeyError:
                # 이미 해제된 경우 무시
                pass

            # 만료 이력 추가
            record = self._order_history.get_record(order_id)
            if record:
                self._order_history.add_record(
                    record.order,
                    OrderStatus.EXPIRED,
                    current_timestamp
                )

        return True

    def reset(self) -> None:
        """거래소 초기화."""
        # 1. Portfolio 초기화 (새로 생성)
        self._portfolio = Portfolio()
        self._portfolio.deposit_currency(self._quote_currency, self._initial_balance)

        # 2. OrderBook 초기화 (새로 생성)
        self._orderbook = OrderBook()

        # 3. OrderHistory 초기화 (새로 생성)
        self._order_history = OrderHistory()

        # 4. MarketData 커서 리셋
        self._market_data.reset()

        # 5. TradeSimulation 재생성
        self._trade_simulation = TradeSimulation(
            maker_fee_ratio=self._maker_fee_ratio,
            taker_fee_ratio=self._taker_fee_ratio
        )

        # 6. Service 컴포넌트 재생성 (Portfolio, OrderHistory 참조 갱신)
        self._order_validator = OrderValidator(self._portfolio, self._market_data)
        self._order_executor = OrderExecutor(
            self._portfolio,
            self._orderbook,
            self._market_data,
            self._trade_simulation,
            self._order_history
        )
        self._position_manager = PositionManager(
            self._portfolio,
            self._market_data,
            self._initial_balance
        )
        self._market_data_service = MarketDataService(self._market_data)

        # 7. 거래 내역 초기화
        self._trade_history = []

    def get_current_timestamp(self) -> int | None:
        """현재 시장 타임스탬프 조회.

        Returns:
            int | None: 타임스탬프
        """
        return self._market_data.get_current_timestamp()

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

    def get_orderbook(self, symbol: str, depth: int = 20):
        """OHLC 기반 더미 호가창 생성 (Gateway API 호환용).

        Args:
            symbol: 심볼 (예: "BTC/USDT")
            depth: 호가 깊이 (기본값: 20)

        Returns:
            Orderbook: financial-assets Orderbook 객체
        """
        return self._market_data_service.generate_orderbook(symbol, depth)

    def get_available_markets(self) -> list[dict]:
        """마켓 목록 조회 (Gateway API 호환용).

        Returns:
            list[dict]: [{"symbol": Symbol, "status": MarketStatus}, ...]
        """
        return self._market_data_service.get_available_markets()
