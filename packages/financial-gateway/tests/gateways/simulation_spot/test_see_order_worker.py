# SeeOrderWorker TDD 테스트

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
from financial_assets.constants import OrderSide, OrderType, OrderStatus, TimeInForce
from financial_assets.order import SpotOrder

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
class SeeOrderRequest(BaseRequest):
    order: SpotOrder


@dataclass
class SeeOrderResponse(BaseResponse):
    order: Optional[SpotOrder] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeOrderWorker:
    # 주문 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeOrderRequest) -> SeeOrderResponse:
        # 주문 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. order_id 추출 (client_order_id 우선)
            order_id = self._get_order_id(request.order)

            # 2. Exchange에서 주문 조회
            order = self.exchange.get_order(order_id)
            receive_when = self._get_timestamp_ms()

            if order is None:
                return self._decode_error(request, "ORDER_NOT_FOUND", f"Order {order_id} not found", send_when, receive_when)

            # 3. Decode: → Response
            return self._decode_success(request, order, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "ORDER_NOT_FOUND", str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_order_id(self, order: SpotOrder) -> str:
        # Simulation Exchange는 order_id로만 조회 가능
        # (실제 거래소 Worker에서는 client_order_id 우선 사용)
        return order.order_id

    def _decode_success(
        self,
        request: SeeOrderRequest,
        order: SpotOrder,
        send_when: int,
        receive_when: int
    ) -> SeeOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order=order
        )

    def _decode_error(
        self,
        request: SeeOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderResponse(
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


class TestSeeOrderWorker:
    # SeeOrderWorker 테스트

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
        # SeeOrderWorker 생성
        return SeeOrderWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_pending_order(self, worker, exchange, btc_address):
        # 미체결 주문 조회
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. LIMIT 주문 생성 (미체결)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,  # 낮은 가격 = 미체결
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order)

        # 2. 주문 조회
        request = SeeOrderRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.order is not None
        assert response.order.order_id == order.order_id

        # 주문 상태 확인 (OrderHistory에서 조회)
        order_status = exchange.get_order_status(order.order_id)
        assert order_status in [OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED]

    def test_see_filled_order(self, worker, exchange, btc_address):
        # 완전 체결된 주문 조회
        # MARKET 주문 (즉시 체결)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.01,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        trades = exchange.place_order(order)

        # 체결 확인
        total_filled = sum(trade.pair.get_asset() for trade in trades)
        if total_filled < 0.01:
            pytest.skip("MARKET order not fully filled")

        # 주문 조회
        request = SeeOrderRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert response.order is not None

        # 주문 상태 확인
        order_status = exchange.get_order_status(order.order_id)
        assert order_status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]

    def test_see_canceled_order(self, worker, exchange, btc_address):
        # 취소된 주문 조회
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. LIMIT 주문 생성
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order)

        # 2. 주문 취소
        exchange.cancel_order(order.order_id)

        # 3. 주문 조회
        request = SeeOrderRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        # 4. 검증
        assert response.is_success is True
        assert response.order is not None

        # 주문 상태 확인
        order_status = exchange.get_order_status(order.order_id)
        assert order_status == OrderStatus.CANCELED

    def test_see_order_with_client_order_id(self, worker, exchange, btc_address):
        # client_order_id로 주문 조회
        current_price = exchange.get_current_price("BTC/USDT")
        client_id = f"my_order_{uuid.uuid4().hex[:8]}"

        # 1. LIMIT 주문 생성
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            client_order_id=client_id,
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order)

        # 2. 주문 조회
        request = SeeOrderRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.order is not None
        assert response.order.client_order_id == client_id

    # ========== 실패 케이스 ==========

    def test_order_not_found(self, worker, exchange, btc_address):
        # 존재하지 않는 주문
        fake_order = SpotOrder(
            order_id="non_existent_order",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=45000.0,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )

        request = SeeOrderRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=fake_order
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code == "ORDER_NOT_FOUND"
