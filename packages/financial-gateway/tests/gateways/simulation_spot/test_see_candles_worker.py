# SeeCandlesWorker TDD 테스트

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
class SeeCandlesRequest(BaseRequest):
    address: StockAddress
    interval: str
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class SeeCandlesResponse(BaseResponse):
    candles: Optional[pd.DataFrame] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeCandlesWorker:
    # 캔들 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeCandlesRequest) -> SeeCandlesResponse:
        # 캔들 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. Exchange에서 캔들 데이터 조회
            candles_df = self.exchange.get_candles(
                symbol=symbol,
                start_time=request.start_time,
                end_time=request.end_time,
                limit=request.limit
            )
            receive_when = self._get_timestamp_ms()

            # 3. Decode: → Response
            return self._decode_success(request, candles_df, send_when, receive_when)

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
        request: SeeCandlesRequest,
        candles_df: pd.DataFrame,
        send_when: int,
        receive_when: int
    ) -> SeeCandlesResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeCandlesResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            candles=candles_df
        )

    def _decode_error(
        self,
        request: SeeCandlesRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeCandlesResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeCandlesResponse(
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


class TestSeeCandlesWorker:
    # SeeCandlesWorker 테스트

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
        # SeeCandlesWorker 생성
        return SeeCandlesWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_all_candles(self, worker, exchange, btc_address):
        # 전체 캔들 조회
        request = SeeCandlesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            interval="1m"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.candles is not None
        assert isinstance(response.candles, pd.DataFrame)
        assert len(response.candles) > 0

        # DataFrame 컬럼 확인
        assert 'timestamp' in response.candles.columns
        assert 'open' in response.candles.columns
        assert 'high' in response.candles.columns
        assert 'low' in response.candles.columns
        assert 'close' in response.candles.columns
        assert 'volume' in response.candles.columns

        # timestamp 오름차순 확인
        timestamps = response.candles['timestamp'].tolist()
        assert timestamps == sorted(timestamps)

    def test_see_candles_with_limit(self, worker, exchange, btc_address):
        # limit 적용
        request = SeeCandlesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            interval="1m",
            limit=10
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.candles is not None
        assert len(response.candles) == 10

    def test_see_candles_with_start_time(self, worker, exchange, btc_address):
        # start_time 적용
        request = SeeCandlesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            interval="1m",
            start_time=1300  # timestamp 1300부터
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.candles is not None
        assert len(response.candles) > 0

        # 모든 timestamp가 start_time 이상
        assert all(response.candles['timestamp'] >= 1300)

    def test_see_candles_with_end_time(self, worker, exchange, btc_address):
        # end_time 적용 (실제 존재하는 timestamp 사용)
        # 1000 + 30*60 = 2800
        request = SeeCandlesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            interval="1m",
            end_time=2800  # timestamp 2800까지
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.candles is not None
        assert len(response.candles) > 0

        # 모든 timestamp가 end_time 이하
        assert all(response.candles['timestamp'] <= 2800)

    def test_see_candles_with_time_range(self, worker, exchange, btc_address):
        # start_time + end_time (실제 존재하는 timestamp 사용)
        # 1000 + 5*60 = 1300, 1000 + 30*60 = 2800
        request = SeeCandlesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            interval="1m",
            start_time=1300,
            end_time=2800
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.candles is not None
        assert len(response.candles) > 0

        # timestamp 범위 확인
        assert all(response.candles['timestamp'] >= 1300)
        assert all(response.candles['timestamp'] <= 2800)

    # ========== 실패 케이스 ==========

    def test_see_candles_invalid_symbol(self, worker, exchange):
        # 존재하지 않는 심볼
        fake_address = StockAddress("candle", "binance", "spot", "INVALID", "USDT", "1m")

        request = SeeCandlesRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=fake_address,
            interval="1m"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is False
        assert response.error_code in ["INVALID_SYMBOL", "API_ERROR"]
        assert response.candles is None
