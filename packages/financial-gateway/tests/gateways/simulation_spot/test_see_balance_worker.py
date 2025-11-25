# SeeBalanceWorker TDD 테스트

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
from financial_assets.constants import OrderSide, OrderType
from financial_assets.order import SpotOrder
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
class SeeBalanceRequest(BaseRequest):
    currencies: Optional[List[str]] = None


@dataclass
class SeeBalanceResponse(BaseResponse):
    balances: Optional[Dict[str, Dict[str, Union[Token, float]]]] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeBalanceWorker:
    # 잔고 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeBalanceRequest) -> SeeBalanceResponse:
        # 잔고 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. 조회할 currencies 결정
            if request.currencies is None or len(request.currencies) == 0:
                # 전체 조회
                currencies = self.exchange._portfolio.get_currencies()
            else:
                currencies = request.currencies

            # 2. 각 currency별 잔고 조회
            balances = {}
            for currency in currencies:
                available = self.exchange._portfolio.get_available_balance(currency)
                locked = self.exchange._portfolio.get_locked_balance(currency)
                total = available + locked

                # 0 잔고 제외 (전체 조회일 때만)
                if request.currencies is None and total < 0.0000001:
                    continue

                # balance Token 생성
                balance_token = Token(currency, total)

                balances[currency] = {
                    "balance": balance_token,
                    "available": available,
                    "promised": locked
                }

            receive_when = self._get_timestamp_ms()

            # 3. Decode: → Response
            return self._decode_success(request, balances, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeBalanceRequest,
        balances: Dict[str, Dict[str, Union[Token, float]]],
        send_when: int,
        receive_when: int
    ) -> SeeBalanceResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeBalanceResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            balances=balances
        )

    def _decode_error(
        self,
        request: SeeBalanceRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeBalanceResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeBalanceResponse(
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


class TestSeeBalanceWorker:
    # SeeBalanceWorker 테스트

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
        # SeeBalanceWorker 생성
        return SeeBalanceWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_all_balances(self, worker, exchange):
        # 전체 잔고 조회
        request = SeeBalanceRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            currencies=None
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.balances is not None
        assert "USDT" in response.balances

        # USDT 잔고 확인
        usdt = response.balances["USDT"]
        assert "balance" in usdt
        assert "available" in usdt
        assert "promised" in usdt

        # Token 객체 확인
        assert isinstance(usdt["balance"], Token)
        assert usdt["balance"].symbol == "USDT"
        assert usdt["balance"].amount == 100000.0

        # available + promised = balance
        assert usdt["available"] + usdt["promised"] == usdt["balance"].amount

    def test_see_specific_currency(self, worker, exchange):
        # 특정 currency 조회
        request = SeeBalanceRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            currencies=["USDT"]
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.balances is not None
        assert len(response.balances) == 1
        assert "USDT" in response.balances

        # USDT 잔고 확인
        usdt = response.balances["USDT"]
        assert usdt["balance"].symbol == "USDT"
        assert usdt["balance"].amount == 100000.0
        assert usdt["available"] == 100000.0
        assert usdt["promised"] == 0.0

    def test_see_balance_with_locked_amount(self, worker, exchange, btc_address):
        # locked amount가 있는 경우
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. LIMIT 주문 생성 (미체결 → USDT locked)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order)

        # 2. 잔고 조회
        request = SeeBalanceRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            currencies=["USDT"]
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        usdt = response.balances["USDT"]

        # locked amount가 있어야 함
        assert usdt["promised"] > 0
        assert usdt["available"] < 100000.0
        assert usdt["available"] + usdt["promised"] == usdt["balance"].amount

    def test_see_balance_empty_currencies_list(self, worker, exchange):
        # 빈 리스트는 None과 동일하게 처리
        request = SeeBalanceRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            currencies=[]
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.balances is not None
        assert "USDT" in response.balances

    def test_see_balance_excludes_zero_balance(self, worker, exchange):
        # 전체 조회 시 0 잔고 제외
        # (초기에는 USDT만 있고 다른 currency는 없음)
        request = SeeBalanceRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            currencies=None
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.balances is not None

        # USDT만 있어야 함 (다른 currency는 0이므로 제외)
        assert "USDT" in response.balances
        # 0 잔고는 포함되지 않아야 함
        for currency, data in response.balances.items():
            assert data["balance"].amount > 0.0000001
