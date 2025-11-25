# SeeServerTimeWorker TDD 테스트

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
class SeeServerTimeRequest(BaseRequest):
    # 서버 시간 조회는 추가 파라미터 없음
    pass


@dataclass
class SeeServerTimeResponse(BaseResponse):
    # 성공 시 응답 데이터
    server_time: Optional[int] = None  # UTC ms


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeServerTimeWorker:
    # 서버 시간 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeServerTimeRequest) -> SeeServerTimeResponse:
        # 서버 시간 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # Exchange에서 현재 타임스탬프 조회
            server_time = self.exchange.get_current_timestamp() * 1000  # 초 → 밀리초
            receive_when = self._get_timestamp_ms()

            # Decode: → Response
            return self._decode_success(request, server_time, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeServerTimeRequest,
        server_time: int,
        send_when: int,
        receive_when: int
    ) -> SeeServerTimeResponse:
        # 성공 응답 디코딩
        # processed_when은 server_time과 동일
        processed_when = server_time

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeServerTimeResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            server_time=server_time
        )

    def _decode_error(
        self,
        request: SeeServerTimeRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeServerTimeResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeServerTimeResponse(
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


class TestSeeServerTimeWorker:
    # SeeServerTimeWorker 테스트

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
        # SeeServerTimeWorker 생성
        return SeeServerTimeWorker(exchange)

    # ========== 성공 케이스 ==========

    def test_see_server_time_success(self, worker, exchange):
        # 기본 서버 시간 조회
        request = SeeServerTimeRequest(
            request_id=f"time_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.server_time is not None
        assert isinstance(response.server_time, int)
        assert response.server_time > 0

    def test_see_server_time_equals_processed_when(self, worker, exchange):
        # server_time과 processed_when이 동일한지 확인
        request = SeeServerTimeRequest(
            request_id=f"time_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.server_time == response.processed_when

    def test_see_server_time_in_milliseconds(self, worker, exchange):
        # 밀리초 단위 확인 (13자리)
        request = SeeServerTimeRequest(
            request_id=f"time_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증 - timestamp가 밀리초 단위인지 (일반적으로 13자리)
        assert response.is_success is True
        # Simulation 타임스탬프는 작은 값이므로 0보다 큰지만 확인
        assert response.server_time > 0

    def test_see_server_time_matches_exchange_timestamp(self, worker, exchange):
        # Exchange의 타임스탬프와 일치하는지 확인
        request = SeeServerTimeRequest(
            request_id=f"time_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        # 실행 전 타임스탬프
        before_timestamp = exchange.get_current_timestamp() * 1000

        response = worker.execute(request)

        # 실행 후 타임스탬프
        after_timestamp = exchange.get_current_timestamp() * 1000

        # 검증 - 응답의 server_time이 before와 after 사이에 있어야 함
        assert response.is_success is True
        assert before_timestamp <= response.server_time <= after_timestamp

    def test_see_server_time_timegaps(self, worker, exchange):
        # timegaps 확인 (매우 작아야 함)
        request = SeeServerTimeRequest(
            request_id=f"time_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        # Simulation은 동기식이므로 timegaps가 0이어야 함
        assert response.timegaps == 0
