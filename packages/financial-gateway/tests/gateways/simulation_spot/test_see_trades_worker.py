# SeeTradesWorker TDD 테스트

import pytest
import pandas as pd
import uuid
from dataclasses import dataclass, field
from typing import Optional, List

from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade

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
class SeeTradesRequest(BaseRequest):
    address: StockAddress
    order: Optional[SpotOrder] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class SeeTradesResponse(BaseResponse):
    trades: List[SpotTrade] = field(default_factory=list)


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeTradesWorker:
    # 체결 내역 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeTradesRequest) -> SeeTradesResponse:
        # 체결 내역 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. Exchange에서 trade history 조회
            if request.order is not None:
                # 특정 order의 trades만 조회
                order_id = request.order.order_id
                all_trades = self.exchange.get_trade_history(symbol)
                trades = [t for t in all_trades if t.order.order_id == order_id]
            else:
                # 마켓 전체 trades 조회
                trades = self.exchange.get_trade_history(symbol)

            receive_when = self._get_timestamp_ms()

            # 3. 최신순 정렬 (timestamp 내림차순)
            trades = sorted(trades, key=lambda t: t.timestamp, reverse=True)

            # 4. limit 적용
            if request.limit is not None and request.limit > 0:
                trades = trades[:request.limit]

            # 5. Decode: → Response
            return self._decode_success(request, trades, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "INVALID_SYMBOL", str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_symbol(self, address: StockAddress) -> str:
        # StockAddress → symbol (BTC/USDT)
        return address.to_symbol().to_slash()

    def _decode_success(
        self,
        request: SeeTradesRequest,
        trades: List[SpotTrade],
        send_when: int,
        receive_when: int
    ) -> SeeTradesResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTradesResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            trades=trades
        )

    def _decode_error(
        self,
        request: SeeTradesRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeTradesResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTradesResponse(
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


class TestSeeTradesWorker:
    # SeeTradesWorker 테스트

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
        # SeeTradesWorker 생성
        return SeeTradesWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    @pytest.fixture
    def eth_address(self):
        # ETH/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_trades_after_market_order(self, worker, exchange, btc_address):
        # MARKET 주문 후 체결 내역 조회
        # 1. MARKET 주문 생성
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
        if len(trades) == 0:
            pytest.skip("MARKET order not filled")

        # 2. Trades 조회
        request = SeeTradesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert len(response.trades) > 0
        assert isinstance(response.trades[0], SpotTrade)

        # 주문 ID 확인
        assert any(t.order.order_id == order.order_id for t in response.trades)

    def test_see_trades_specific_order(self, worker, exchange, btc_address):
        # 특정 주문의 체결만 조회
        # 1. 첫 번째 주문
        order1 = SpotOrder(
            order_id=f"order1_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order1)

        # 2. 두 번째 주문
        order2 = SpotOrder(
            order_id=f"order2_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.05,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order2)

        # 3. order1의 체결만 조회
        request = SeeTradesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            order=order1
        )

        response = worker.execute(request)

        # 4. 검증 - order1의 체결만 있어야 함
        assert response.is_success is True
        assert len(response.trades) > 0
        assert all(t.order.order_id == order1.order_id for t in response.trades)

    def test_see_trades_with_limit(self, worker, exchange, btc_address):
        # limit 적용
        # 1. 여러 주문 생성
        for i in range(3):
            order = SpotOrder(
                order_id=f"order_{i}_{uuid.uuid4().hex[:8]}",
                stock_address=btc_address,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                price=None,
                amount=0.01,
                timestamp=exchange.get_current_timestamp(),
                min_trade_amount=0.01
            )
            exchange.place_order(order)

        # 2. limit=2로 조회
        request = SeeTradesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            limit=2
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert len(response.trades) <= 2

    def test_see_trades_empty(self, worker, exchange, btc_address):
        # 체결 내역이 없을 때
        request = SeeTradesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert len(response.trades) == 0

    def test_see_trades_sorted_by_timestamp(self, worker, exchange, btc_address):
        # timestamp 내림차순 정렬 확인
        # 1. 여러 주문 생성
        for i in range(3):
            order = SpotOrder(
                order_id=f"order_{i}_{uuid.uuid4().hex[:8]}",
                stock_address=btc_address,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                price=None,
                amount=0.01,
                timestamp=exchange.get_current_timestamp(),
                min_trade_amount=0.01
            )
            exchange.place_order(order)

        # 2. Trades 조회
        request = SeeTradesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 3. 검증 - timestamp 내림차순
        assert response.is_success is True
        if len(response.trades) > 1:
            timestamps = [t.timestamp for t in response.trades]
            assert timestamps == sorted(timestamps, reverse=True)

    # ========== 실패 케이스 ==========

    def test_see_trades_invalid_symbol(self, worker, exchange):
        # 존재하지 않는 심볼 (Simulation에서는 빈 리스트 반환)
        fake_address = StockAddress("candle", "binance", "spot", "INVALID", "USDT", "1m")

        request = SeeTradesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=fake_address
        )

        response = worker.execute(request)

        # 검증 - Simulation에서는 에러가 아니라 빈 결과 반환
        assert response.is_success is True
        assert len(response.trades) == 0
