# SeeAvailableMarketsWorker TDD 테스트

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
from financial_assets.symbol import Symbol
from financial_assets.market_info import MarketInfo
from financial_assets.constants import MarketStatus

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
class SeeAvailableMarketsRequest(BaseRequest):
    # 조회 개수 제한 (None이면 게이트웨이 기본값 또는 전체 조회)
    limit: Optional[int] = None


@dataclass
class SeeAvailableMarketsResponse(BaseResponse):
    # 성공 시 응답 데이터
    markets: List[MarketInfo] = field(default_factory=list)


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeAvailableMarketsWorker:
    # 거래 가능 마켓 목록 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeAvailableMarketsRequest) -> SeeAvailableMarketsResponse:
        # 마켓 목록 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # Exchange에서 마켓 목록 조회
            markets_data = self.exchange.get_available_markets()
            receive_when = self._get_timestamp_ms()

            # dict → MarketInfo 변환
            markets = []
            for market_dict in markets_data:
                market_info = MarketInfo(
                    symbol=market_dict["symbol"],
                    status=market_dict["status"]
                )
                markets.append(market_info)

            # limit 적용
            if request.limit is not None and request.limit > 0:
                markets = markets[:request.limit]

            # Decode: → Response
            return self._decode_success(request, markets, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeAvailableMarketsRequest,
        markets: List[MarketInfo],
        send_when: int,
        receive_when: int
    ) -> SeeAvailableMarketsResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeAvailableMarketsResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            markets=markets
        )

    def _decode_error(
        self,
        request: SeeAvailableMarketsRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeAvailableMarketsResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeAvailableMarketsResponse(
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


class TestSeeAvailableMarketsWorker:
    # SeeAvailableMarketsWorker 테스트

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

        # SOL/USDT 캔들 데이터
        sol_addr = StockAddress("candle", "binance", "spot", "SOL", "USDT", "1m")
        sol_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(100)],
            'open': [100.0 + i for i in range(100)],
            'high': [105.0 + i for i in range(100)],
            'low': [95.0 + i for i in range(100)],
            'close': [100.0 + i for i in range(100)],
            'volume': [300.0] * 100
        })
        sol_candle = Candle(sol_addr, sol_df)

        # MultiCandle 생성
        mc = MultiCandle([btc_candle, eth_candle, sol_candle])
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
        # SeeAvailableMarketsWorker 생성
        return SeeAvailableMarketsWorker(exchange)

    # ========== 성공 케이스 ==========

    def test_see_available_markets_all(self, worker, exchange):
        # 전체 마켓 조회
        request = SeeAvailableMarketsRequest(
            request_id=f"markets_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert len(response.markets) == 3  # BTC, ETH, SOL
        assert all(isinstance(m, MarketInfo) for m in response.markets)

        # 심볼 확인
        symbols = [m.symbol for m in response.markets]
        assert Symbol("BTC/USDT") in symbols
        assert Symbol("ETH/USDT") in symbols
        assert Symbol("SOL/USDT") in symbols

    def test_see_available_markets_status(self, worker, exchange):
        # 모든 마켓이 TRADING 상태인지 확인
        request = SeeAvailableMarketsRequest(
            request_id=f"markets_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증 - Simulation은 모두 TRADING
        assert response.is_success is True
        assert all(m.status == MarketStatus.TRADING for m in response.markets)

    def test_see_available_markets_with_limit(self, worker, exchange):
        # limit 적용
        request = SeeAvailableMarketsRequest(
            request_id=f"markets_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            limit=2
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert len(response.markets) == 2

    def test_see_available_markets_symbol_structure(self, worker, exchange):
        # Symbol 객체 구조 확인
        request = SeeAvailableMarketsRequest(
            request_id=f"markets_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        for market in response.markets:
            assert isinstance(market.symbol, Symbol)
            assert market.symbol.base is not None
            assert market.symbol.quote is not None
            # Simulation은 모두 USDT 마켓
            assert market.symbol.quote == "USDT"

    def test_see_available_markets_timegaps(self, worker, exchange):
        # timegaps 확인 (매우 작아야 함)
        request = SeeAvailableMarketsRequest(
            request_id=f"markets_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation"
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        # Simulation은 동기식이므로 timegaps가 0이어야 함
        assert response.timegaps == 0
