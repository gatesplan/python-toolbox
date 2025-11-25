# SeeTickerWorker TDD 테스트

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
class SeeTickerRequest(BaseRequest):
    address: StockAddress


@dataclass
class SeeTickerResponse(BaseResponse):
    current: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeTickerWorker:
    # 시세 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeTickerRequest) -> SeeTickerResponse:
        # 시세 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. MarketData에서 현재 가격 정보 조회
            price_data = self.exchange._market_data.get_current(symbol)
            receive_when = self._get_timestamp_ms()

            if price_data is None:
                return self._decode_error(request, "INVALID_SYMBOL", f"Symbol {symbol} not found", send_when, receive_when)

            # 3. Decode: Price → Response
            return self._decode_success(request, price_data, send_when, receive_when)

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
        request: SeeTickerRequest,
        price_data,
        send_when: int,
        receive_when: int
    ) -> SeeTickerResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTickerResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            current=price_data.c,
            open=price_data.o,
            high=price_data.h,
            low=price_data.l,
            volume=price_data.v
        )

    def _decode_error(
        self,
        request: SeeTickerRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeTickerResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTickerResponse(
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


class TestSeeTickerWorker:
    # SeeTickerWorker 테스트

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
        # SeeTickerWorker 생성
        return SeeTickerWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    @pytest.fixture
    def eth_address(self):
        # ETH/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_ticker_btc(self, worker, exchange, btc_address):
        # BTC 시세 조회
        request = SeeTickerRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.current is not None
        assert response.open is not None
        assert response.high is not None
        assert response.low is not None
        assert response.volume is not None

        # 가격 관계 검증 (high >= current >= low)
        assert response.high >= response.current
        assert response.current >= response.low

        # open도 범위 내에 있어야 함
        assert response.high >= response.open
        assert response.open >= response.low

        # volume은 양수
        assert response.volume > 0

    def test_see_ticker_eth(self, worker, exchange, eth_address):
        # ETH 시세 조회
        request = SeeTickerRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=eth_address
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.current is not None
        assert response.high >= response.current >= response.low

    # ========== 실패 케이스 ==========

    def test_see_ticker_invalid_symbol(self, worker, exchange):
        # 존재하지 않는 심볼
        fake_address = StockAddress("candle", "binance", "spot", "INVALID", "USDT", "1m")

        request = SeeTickerRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=fake_address
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is False
        assert response.error_code == "INVALID_SYMBOL"
        assert response.current is None
