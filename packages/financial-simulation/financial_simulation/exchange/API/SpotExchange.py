# Spot 거래소 API Layer - 외부 진입점으로 주문, 잔고, 포지션 관리

from __future__ import annotations

from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.constants import OrderStatus
from financial_assets.symbol import Symbol
from simple_logger import init_logging, func_logging, logger
from ..Core import Portfolio, OrderBook, MarketData, OrderHistory, OrderRecord
from ..Service import OrderValidator, OrderExecutor, PositionManager, MarketDataService
from ...tradesim.API import TradeSimulation


class SpotExchange:
    # Spot 거래소 API Layer

    @init_logging(level="INFO")
    def __init__(
        self,
        initial_balance: float,
        market_data: MarketData,
        maker_fee_ratio: float = 0.001,
        taker_fee_ratio: float = 0.002,
        quote_currency: str = "USDT"
    ):
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
        self._trade_index_by_order: dict[str, list[int]] = {}

        logger.info("SpotExchange 초기화 완료")

    @func_logging(level="INFO")
    def place_order(self, order: SpotOrder) -> list[SpotTrade]:
        # 주문 실행 (잔고/자산 부족 시 ValueError)
        self._order_validator.validate_order(order)
        trades = self._order_executor.execute_order(order)

        # 거래 내역 추가 및 인덱스 업데이트
        for trade in trades:
            index = len(self._trade_history)
            self._trade_history.append(trade)

            order_id = trade.order.order_id
            if order_id not in self._trade_index_by_order:
                self._trade_index_by_order[order_id] = []
            self._trade_index_by_order[order_id].append(index)

        return trades

    @func_logging(level="INFO")
    def cancel_order(self, order_id: str) -> None:
        # 미체결 주문 취소 (주문 없으면 KeyError)
        self._order_executor.cancel_order(order_id)

    def get_order(self, order_id: str) -> SpotOrder | None:
        # 개별 주문 조회 (미체결 + 이력)
        order = self._orderbook.get_order(order_id)
        if order is not None:
            return order

        record = self._order_history.get_record(order_id)
        return record.order if record else None

    def get_order_status(self, order_id: str) -> OrderStatus | None:
        # 주문 상태 조회
        order = self._orderbook.get_order(order_id)
        if order is not None:
            record = self._order_history.get_record(order_id)
            return record.status if record else OrderStatus.NEW

        record = self._order_history.get_record(order_id)
        return record.status if record else None

    def get_open_orders(self, symbol: str | Symbol | None = None) -> list[SpotOrder]:
        # 미체결 주문 조회
        if symbol is None:
            return self._orderbook.get_all_orders()
        return self._orderbook.get_orders_by_symbol(str(symbol))

    def get_trade_history(self, symbol: str | Symbol | None = None) -> list[SpotTrade]:
        # 거래 내역 조회
        if symbol is None:
            return self._trade_history

        symbol_str = str(symbol)
        return [
            trade for trade in self._trade_history
            if trade.order.stock_address.to_symbol().to_slash() == symbol_str
        ]

    def get_trades_by_order_id(self, order_id: str) -> list[SpotTrade]:
        # order_id로 거래 내역 조회 (O(1) + O(k) 성능)
        indices = self._trade_index_by_order.get(order_id, [])
        return [self._trade_history[i] for i in indices]

    def get_balance(self, currency: str | None = None) -> float | dict[str, float]:
        # Currency 잔고 조회 (사용 가능 잔고)
        # NOTE: Quote Currency(USDT, USD) 전용. Base Asset(BTC, ETH)는 get_position() 사용
        if currency is None:
            currencies = self._portfolio.get_currencies()
            return {curr: self._portfolio.get_available_balance(curr) for curr in currencies}
        else:
            return self._portfolio.get_available_balance(currency)

    def get_locked_balance(self, currency: str) -> float:
        # 잠긴 잔고 조회 (미체결 매수 주문용)
        return self._portfolio.get_locked_balance(currency)

    def get_currencies(self) -> list[str]:
        # 보유 화폐 목록 조회
        return self._portfolio.get_currencies()

    def get_positions(self) -> dict[str, float]:
        # 보유 포지션 조회 {ticker: amount}
        return self._position_manager.get_positions()

    def get_position_value(self, symbol: str | Symbol) -> dict[str, float]:
        # 특정 포지션의 상세 가치 정보 (book_value, market_value, pnl, pnl_ratio)
        ticker = symbol.to_dash() if isinstance(symbol, Symbol) else Symbol(symbol).to_dash()
        return {
            "book_value": self._position_manager.get_position_book_value(ticker),
            "market_value": self._position_manager.get_position_market_value(ticker),
            "pnl": self._position_manager.get_position_pnl(ticker),
            "pnl_ratio": self._position_manager.get_position_pnl_ratio(ticker)
        }

    def get_position(self, symbol: str | Symbol) -> float:
        # 단일 포지션 수량 조회 (없으면 0.0)
        ticker = symbol.to_dash() if isinstance(symbol, Symbol) else Symbol(symbol).to_dash()
        return self._portfolio.get_positions().get(ticker, 0.0)

    def get_available_position(self, symbol: str | Symbol) -> float:
        # 사용 가능 포지션 조회 (매도 가능 수량)
        ticker = symbol.to_dash() if isinstance(symbol, Symbol) else Symbol(symbol).to_dash()
        return self._portfolio.get_available_position(ticker)

    def get_locked_position(self, symbol: str | Symbol) -> float:
        # 잠긴 포지션 조회 (미체결 매도 주문용)
        ticker = symbol.to_dash() if isinstance(symbol, Symbol) else Symbol(symbol).to_dash()
        return self._portfolio.get_locked_position(ticker)

    def get_total_value(self) -> float:
        # 총 자산 가치 (quote_currency 기준)
        return self._position_manager.get_total_value(quote_currency=self._quote_currency)

    def get_statistics(self) -> dict[str, float]:
        # 포트폴리오 통계 조회
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

    @func_logging(level="INFO")
    def step(self) -> bool:
        # 다음 시장 틱으로 이동 (계속 가능하면 True, 종료면 False)
        can_continue = self._market_data.step()

        if not can_continue:
            return False

        # GTD 주문 만료 처리
        current_timestamp = self._market_data.get_current_timestamp()
        expired_order_ids = self._orderbook.expire_orders(current_timestamp)

        # 만료된 주문의 자산 잠금 해제 및 이력 추가
        for order_id in expired_order_ids:
            try:
                self._portfolio.unlock_currency(order_id)
            except KeyError:
                pass

            record = self._order_history.get_record(order_id)
            if record:
                self._order_history.add_record(
                    record.order,
                    OrderStatus.EXPIRED,
                    current_timestamp
                )

        return True

    @func_logging(level="INFO")
    def reset(self) -> None:
        # 거래소 초기화
        self._portfolio = Portfolio()
        self._portfolio.deposit_currency(self._quote_currency, self._initial_balance)

        self._orderbook = OrderBook()
        self._order_history = OrderHistory()
        self._market_data.reset()

        self._trade_simulation = TradeSimulation(
            maker_fee_ratio=self._maker_fee_ratio,
            taker_fee_ratio=self._taker_fee_ratio
        )

        # Service 컴포넌트 재생성
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

        # 거래 내역 초기화
        self._trade_history = []
        self._trade_index_by_order = {}

        logger.info("SpotExchange 리셋 완료")

    def get_current_timestamp(self) -> int | None:
        # 현재 시장 타임스탬프 조회
        return self._market_data.get_current_timestamp()

    def get_current_price(self, symbol: str | Symbol) -> float | None:
        # 현재 시장 가격 조회
        price_data = self._market_data.get_current(str(symbol))
        if price_data is None:
            return None
        return price_data.c

    def is_finished(self) -> bool:
        # 시뮬레이션 종료 여부
        return self._market_data.is_finished()

    def get_orderbook(self, symbol: str | Symbol, depth: int = 20):
        # OHLC 기반 더미 호가창 생성 (Gateway API 호환용)
        return self._market_data_service.generate_orderbook(str(symbol), depth)

    def get_available_markets(self) -> list[dict]:
        # 마켓 목록 조회 (Gateway API 호환용)
        return self._market_data_service.get_available_markets()

    def get_candles(
        self,
        symbol: str | Symbol,
        start_time: int = None,
        end_time: int = None,
        limit: int = None
    ):
        # 과거 캔들 데이터 조회 (Gateway API 호환용)
        return self._market_data.get_candles(
            symbol=str(symbol),
            start_ts=start_time,
            end_ts=end_time,
            limit=limit
        )
