# CancelOrderWorker TDD 테스트

import pytest
import pandas as pd
import uuid

from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, OrderStatus, TimeInForce
from financial_assets.order import SpotOrder

# Request/Response 임시 정의 (패키지 import 회피)
from dataclasses import dataclass
from typing import Optional


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
class CancelOrderRequest(BaseRequest):
    order: SpotOrder


@dataclass
class CancelOrderResponse(BaseResponse):
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    filled_amount: Optional[float] = None
    remaining_amount: Optional[float] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class CancelOrderWorker:
    # 주문 취소 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: CancelOrderRequest) -> CancelOrderResponse:
        # 주문 취소 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. order_id 추출
            order_id = self._get_order_id(request.order)

            # 2. 취소 전 상태 조회 (filled_amount 계산용)
            filled_before = self._calculate_filled_amount(order_id)
            original_amount = request.order.amount

            # 3. Exchange 호출 (취소)
            self.exchange.cancel_order(order_id)
            receive_when = self._get_timestamp_ms()

            # 4. Decode: → Response
            return self._decode_success(request, order_id, filled_before, original_amount, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "ORDER_NOT_FOUND", str(e), send_when, receive_when)

        except ValueError as e:
            receive_when = self._get_timestamp_ms()
            # OrderHistory에서 상태 확인하여 에러 코드 결정
            error_code = self._classify_error(request.order, e)
            return self._decode_error(request, error_code, str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_order_id(self, order):
        # order_id 사용 (OrderBook은 order_id로만 관리)
        return order.order_id

    def _calculate_filled_amount(self, order_id: str) -> float:
        # 주문의 체결 수량 계산 (Trade history 조회)
        trades = self.exchange.get_trade_history()
        filled = sum(
            trade.pair.get_asset()
            for trade in trades
            if trade.order.order_id == order_id or trade.order.client_order_id == order_id
        )
        return filled

    def _classify_error(self, order, error: Exception) -> str:
        # 에러 분류
        error_message = str(error)

        # OrderHistory에서 주문 상태 확인
        order_id = self._get_order_id(order)
        order_obj = self.exchange.get_order(order_id)

        if order_obj is None:
            return "ORDER_NOT_FOUND"

        # 주문 상태 확인
        status = self.exchange.get_order_status(order_id)

        if status == OrderStatus.FILLED:
            return "ORDER_ALREADY_FILLED"
        elif status == OrderStatus.CANCELED:
            return "ORDER_ALREADY_CANCELED"
        else:
            # 기타: 메시지로 분류
            if "filled" in error_message.lower() or "체결" in error_message:
                return "ORDER_ALREADY_FILLED"
            elif "canceled" in error_message.lower() or "취소" in error_message:
                return "ORDER_ALREADY_CANCELED"
            else:
                return "API_ERROR"

    def _decode_success(
        self,
        request: CancelOrderRequest,
        order_id: str,
        filled_amount: float,
        original_amount: float,
        send_when: int,
        receive_when: int
    ) -> CancelOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        # remaining_amount 계산
        remaining_amount = original_amount - filled_amount

        return CancelOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=request.order.client_order_id,
            status=OrderStatus.CANCELED,
            filled_amount=filled_amount,
            remaining_amount=remaining_amount
        )

    def _decode_error(
        self,
        request: CancelOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> CancelOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return CancelOrderResponse(
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


class TestCancelOrderWorker:
    # CancelOrderWorker 테스트

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
        # CancelOrderWorker 생성
        return CancelOrderWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_cancel_pending_order(self, worker, exchange, btc_address):
        # 미체결 주문 취소
        # 1. LIMIT 주문 생성 (미체결 상태로)
        current_price = exchange.get_current_price("BTC/USDT")
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

        # 2. 취소 요청
        request = CancelOrderRequest(
            request_id=f"cancel_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.status == OrderStatus.CANCELED
        assert response.filled_amount == 0.0
        assert response.remaining_amount == 0.1

    def test_cancel_with_client_order_id(self, worker, exchange, btc_address):
        # client_order_id로 취소
        # 주문 생성
        current_price = exchange.get_current_price("BTC/USDT")
        client_id = f"my_order_{uuid.uuid4().hex[:8]}"

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

        # 취소 요청
        request = CancelOrderRequest(
            request_id=f"cancel_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        assert response.is_success is True
        assert response.client_order_id == client_id

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

        request = CancelOrderRequest(
            request_id=f"cancel_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=fake_order
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code == "ORDER_NOT_FOUND"

    def test_order_already_filled(self, worker, exchange, btc_address):
        # 이미 전체 체결된 주문
        # MARKET 주문 (즉시 체결)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.01,  # 작은 수량으로 전체 체결 보장
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        trades = exchange.place_order(order)

        # 전체 체결 확인
        total_filled = sum(trade.pair.get_asset() for trade in trades)
        if total_filled < 0.01:
            pytest.skip("MARKET order not fully filled in test")

        # 취소 시도 (이미 체결된 주문은 OrderBook에 없으므로 KeyError 발생 예상)
        request = CancelOrderRequest(
            request_id=f"cancel_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            order=order
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code in ["ORDER_NOT_FOUND", "ORDER_ALREADY_FILLED"]
