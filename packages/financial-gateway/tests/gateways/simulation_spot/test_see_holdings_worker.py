# SeeHoldingsWorker TDD 테스트

import pytest
import pandas as pd
import uuid
from dataclasses import dataclass
from typing import Optional, Dict, Union, List

from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.symbol import Symbol
from financial_assets.constants import OrderSide, OrderType
from financial_assets.order import SpotOrder
from financial_assets.pair import Pair
from financial_assets.token import Token

# Request/Response 임시 정의 (패키지 import 회피)
@dataclass
class BaseRequest:
    request_id: str
    gateway_name: str


@dataclass
class BaseResponse:
    request_id: str
    is_success: bool
    send_when: int
    receive_when: int
    processed_when: int
    timegaps: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SeeHoldingsRequest(BaseRequest):
    symbols: Optional[List[Symbol]] = None


@dataclass
class SeeHoldingsResponse(BaseResponse):
    holdings: Optional[Dict[str, Dict[str, Union[Pair, float]]]] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeHoldingsWorker:
    # 보유 자산 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeHoldingsRequest) -> SeeHoldingsResponse:
        # 보유 자산 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. 조회할 positions 결정
            all_positions = self.exchange.get_positions()

            if request.symbols is None or len(request.symbols) == 0:
                # 전체 조회 - 0.001 미만 제외
                tickers = [ticker for ticker, amount in all_positions.items() if amount >= 0.001]
            else:
                # 특정 symbols 조회
                tickers = [symbol.to_dash() for symbol in request.symbols]

            # 2. 각 ticker별 holdings 조회
            holdings = {}
            for ticker in tickers:
                # ticker → Symbol (BTC-USDT → Symbol("BTC-USDT"))
                symbol = Symbol(ticker)
                base = symbol.base
                quote = symbol.quote

                # 총 보유량
                total_amount = all_positions.get(ticker, 0.0)

                # available/locked
                available = self.exchange._portfolio.get_available_position(ticker)
                locked = self.exchange._portfolio.get_locked_position(ticker)

                # book_value (평단가 * 수량)
                book_value = self.exchange._position_manager.get_position_book_value(ticker)

                # Pair 생성
                balance_pair = Pair(
                    asset=Token(base, total_amount),
                    value=Token(quote, book_value)
                )

                holdings[base] = {
                    "balance": balance_pair,
                    "available": available,
                    "promised": locked
                }

            receive_when = self._get_timestamp_ms()

            # 3. Decode: → Response
            return self._decode_success(request, holdings, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeHoldingsRequest,
        holdings: Dict[str, Dict[str, Union[Pair, float]]],
        send_when: int,
        receive_when: int
    ) -> SeeHoldingsResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeHoldingsResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            holdings=holdings
        )

    def _decode_error(
        self,
        request: SeeHoldingsRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeHoldingsResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeHoldingsResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=error_message
        )

    def _get_timestamp_ms(self) -> int:
        # 현재 시뮬레이션 타임스탬프 (초 → 밀리초 변환)
        return self.exchange.get_current_timestamp() * 1000


class TestSeeHoldingsWorker:
    # SeeHoldingsWorker 테스트

    @pytest.fixture
    def market_data(self):
        # 테스트용 MarketData 생성
        # BTC/USDT 캔들 데이터
        btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(100)],
            'open': [45000.0 + i * 10 for i in range(100)],
            'high': [45500.0 + i * 10 for i in range(100)],
            'low': [44500.0 + i * 10 for i in range(100)],
            'close': [45000.0 + i * 10 for i in range(100)],
            'volume': [100.0] * 100
        })
        btc_candle = Candle(btc_addr, btc_df)

        # ETH/USDT 캔들 데이터
        eth_addr = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(100)],
            'open': [3000.0 + i * 5 for i in range(100)],
            'high': [3050.0 + i * 5 for i in range(100)],
            'low': [2950.0 + i * 5 for i in range(100)],
            'close': [3000.0 + i * 5 for i in range(100)],
            'volume': [200.0] * 100
        })
        eth_candle = Candle(eth_addr, eth_df)

        # MultiCandle 생성
        mc = MultiCandle([btc_candle, eth_candle])
        return MarketData(mc, start_offset=10)

    @pytest.fixture
    def exchange(self, market_data):
        # 테스트용 SpotExchange 생성
        return SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

    @pytest.fixture
    def worker(self, exchange):
        # SeeHoldingsWorker 생성
        return SeeHoldingsWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    @pytest.fixture
    def eth_address(self):
        # ETH/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_holdings_with_positions(self, worker, exchange, btc_address):
        # 보유 자산이 있는 경우
        # 1. BTC 매수 (MARKET)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        trades = exchange.place_order(order)

        # 체결 확인
        total_filled = sum(trade.pair.get_asset() for trade in trades)
        if total_filled < 0.01:
            pytest.skip("MARKET order not filled enough")

        # 2. Holdings 조회
        request = SeeHoldingsRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            symbols=None
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.holdings is not None
        assert "BTC" in response.holdings

        # BTC holdings 확인
        btc = response.holdings["BTC"]
        assert "balance" in btc
        assert "available" in btc
        assert "promised" in btc

        # Pair 객체 확인
        assert isinstance(btc["balance"], Pair)
        assert btc["balance"].get_asset_token().symbol == "BTC"
        assert btc["balance"].get_value_token().symbol == "USDT"
        assert btc["balance"].get_asset_token().amount > 0

        # available + promised = balance
        assert abs(btc["available"] + btc["promised"] - btc["balance"].get_asset_token().amount) < 0.0001

    def test_see_holdings_empty(self, worker, exchange):
        # 보유 자산이 없는 경우
        request = SeeHoldingsRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            symbols=None
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.holdings is not None
        assert len(response.holdings) == 0

    def test_see_holdings_specific_symbols(self, worker, exchange, btc_address, eth_address):
        # 특정 symbols 조회
        # 1. BTC, ETH 매수
        btc_order = SpotOrder(
            order_id=f"btc_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(btc_order)

        eth_order = SpotOrder(
            order_id=f"eth_{uuid.uuid4().hex[:8]}",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(eth_order)

        # 2. BTC만 조회
        request = SeeHoldingsRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            symbols=[Symbol("BTC/USDT")]
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.holdings is not None
        assert "BTC" in response.holdings

        # BTC만 있어야 함
        btc = response.holdings["BTC"]
        assert btc["balance"].get_asset_token().symbol == "BTC"

    def test_see_holdings_with_locked(self, worker, exchange, btc_address):
        # locked amount가 있는 경우
        # 1. BTC 매수
        buy_order = SpotOrder(
            order_id=f"buy_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(buy_order)

        # 2. LIMIT 매도 주문 (미체결 → BTC locked)
        current_price = exchange.get_current_price("BTC/USDT")
        sell_order = SpotOrder(
            order_id=f"sell_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=current_price * 2.0,  # 높은 가격 = 미체결
            amount=0.05,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(sell_order)

        # 3. Holdings 조회
        request = SeeHoldingsRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            symbols=None
        )

        response = worker.execute(request)

        # 4. 검증
        assert response.is_success is True
        btc = response.holdings["BTC"]

        # locked amount가 있어야 함
        assert btc["promised"] > 0
        assert btc["available"] < btc["balance"].get_asset_token().amount

    def test_see_holdings_empty_symbols_list(self, worker, exchange, btc_address):
        # 빈 리스트는 None과 동일하게 처리
        # 1. BTC 매수
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order)

        # 2. 빈 리스트로 조회
        request = SeeHoldingsRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            symbols=[]
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.holdings is not None
        assert "BTC" in response.holdings
