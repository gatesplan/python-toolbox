# SeeOrderbookWorker TDD 테스트

import pytest
import pandas as pd
import uuid
from dataclasses import dataclass
from typing import Optional

from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.orderbook import Orderbook

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
class SeeOrderbookRequest(BaseRequest):
    address: StockAddress
    limit: Optional[int] = None


@dataclass
class SeeOrderbookResponse(BaseResponse):
    orderbook: Optional[Orderbook] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeOrderbookWorker:
    # 호가창 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeOrderbookRequest) -> SeeOrderbookResponse:
        # 호가창 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. depth 결정 (limit이 None이면 기본값 10)
            depth = request.limit if request.limit is not None else 10

            # 3. Exchange에서 호가창 생성
            orderbook = self.exchange.get_orderbook(symbol, depth=depth)
            receive_when = self._get_timestamp_ms()

            # 4. Decode: → Response
            return self._decode_success(request, orderbook, send_when, receive_when)

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
        request: SeeOrderbookRequest,
        orderbook: Orderbook,
        send_when: int,
        receive_when: int
    ) -> SeeOrderbookResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderbookResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            orderbook=orderbook
        )

    def _decode_error(
        self,
        request: SeeOrderbookRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeOrderbookResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderbookResponse(
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


class TestSeeOrderbookWorker:
    # SeeOrderbookWorker 테스트

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

        # MultiCandle 생성
        mc = MultiCandle([btc_candle])
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
        # SeeOrderbookWorker 생성
        return SeeOrderbookWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_orderbook_default_limit(self, worker, exchange, btc_address):
        # 기본 limit (10)로 호가창 조회
        request = SeeOrderbookRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.orderbook is not None
        assert isinstance(response.orderbook, Orderbook)

        # asks와 bids 확인
        assert len(response.orderbook.asks) == 10
        assert len(response.orderbook.bids) == 10

        # asks 가격 오름차순 확인
        ask_prices = [level.price for level in response.orderbook.asks]
        assert ask_prices == sorted(ask_prices)

        # bids 가격 내림차순 확인
        bid_prices = [level.price for level in response.orderbook.bids]
        assert bid_prices == sorted(bid_prices, reverse=True)

        # 베스트 매도가 > 베스트 매수가
        assert response.orderbook.asks[0].price > response.orderbook.bids[0].price

    def test_see_orderbook_custom_limit(self, worker, exchange, btc_address):
        # 사용자 지정 limit
        request = SeeOrderbookRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            limit=5
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.orderbook is not None
        assert len(response.orderbook.asks) == 5
        assert len(response.orderbook.bids) == 5

    def test_see_orderbook_large_limit(self, worker, exchange, btc_address):
        # 큰 limit
        request = SeeOrderbookRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            limit=100
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.orderbook is not None
        assert len(response.orderbook.asks) == 100
        assert len(response.orderbook.bids) == 100

    def test_see_orderbook_price_and_size(self, worker, exchange, btc_address):
        # price와 size 값 확인
        request = SeeOrderbookRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            limit=10
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True

        # 모든 레벨에 price와 size가 있어야 함
        for level in response.orderbook.asks:
            assert level.price > 0
            assert level.size > 0

        for level in response.orderbook.bids:
            assert level.price > 0
            assert level.size > 0

    # ========== 실패 케이스 ==========

    def test_see_orderbook_invalid_symbol(self, worker, exchange):
        # 존재하지 않는 심볼
        fake_address = StockAddress("candle", "binance", "spot", "INVALID", "USDT", "1m")

        request = SeeOrderbookRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=fake_address
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is False
        assert response.error_code in ["INVALID_SYMBOL", "API_ERROR"]
        assert response.orderbook is None
