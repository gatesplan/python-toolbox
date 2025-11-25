# ModifyOrReplaceOrderWorker TDD 테스트

import pytest
import pandas as pd
import uuid
from dataclasses import dataclass
from typing import Optional, List

from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, OrderStatus, TimeInForce
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
class ModifyOrReplaceOrderRequest(BaseRequest):
    original_order: SpotOrder
    side: Optional[OrderSide] = None
    order_type: Optional[OrderType] = None
    asset_quantity: Optional[float] = None
    price: Optional[float] = None
    quote_quantity: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Optional[TimeInForce] = None
    post_only: Optional[bool] = None
    client_order_id: Optional[str] = None


@dataclass
class ModifyOrReplaceOrderResponse(BaseResponse):
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    trades: Optional[List[SpotTrade]] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class ModifyOrReplaceOrderWorker:
    # 주문 수정/교체 Worker (Simulation)
    # Simulation에서는 modify가 없으므로 취소 후 재생성으로 구현

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: ModifyOrReplaceOrderRequest) -> ModifyOrReplaceOrderResponse:
        # 주문 수정/교체 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. 기존 주문 조회
            order_id = request.original_order.order_id
            existing_order = self.exchange.get_order(order_id)

            if existing_order is None:
                receive_when = self._get_timestamp_ms()
                return self._decode_error(request, "ORDER_NOT_FOUND", f"Order {order_id} not found", send_when, receive_when)

            # 2. 주문 상태 확인 (이미 체결된 경우 에러)
            order_status = self.exchange.get_order_status(order_id)
            if order_status == OrderStatus.FILLED:
                receive_when = self._get_timestamp_ms()
                return self._decode_error(request, "ORDER_ALREADY_FILLED", f"Order {order_id} is already filled", send_when, receive_when)

            # 3. 기존 주문 취소
            self.exchange.cancel_order(order_id)

            # 4. 새 파라미터로 주문 생성
            new_order = self._create_new_order(request, existing_order)
            trades = self.exchange.place_order(new_order)
            receive_when = self._get_timestamp_ms()

            # 5. Decode: → Response
            return self._decode_success(request, new_order, trades, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "ORDER_NOT_FOUND", str(e), send_when, receive_when)

        except ValueError as e:
            receive_when = self._get_timestamp_ms()
            error_message = str(e)

            # 에러 메시지로 에러 코드 분류
            if "balance" in error_message.lower() or "insufficient" in error_message.lower() or "잔고" in error_message:
                error_code = "INSUFFICIENT_BALANCE"
            elif "amount" in error_message.lower() or "quantity" in error_message.lower() or "수량" in error_message or "유효하지" in error_message:
                error_code = "INVALID_QUANTITY"
            else:
                error_code = "INVALID_PARAMETERS"

            return self._decode_error(request, error_code, error_message, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _create_new_order(self, request: ModifyOrReplaceOrderRequest, existing_order: SpotOrder) -> SpotOrder:
        # 새 주문 파라미터 결정 (None이면 기존값 유지)
        side = request.side if request.side is not None else existing_order.side
        order_type = request.order_type if request.order_type is not None else existing_order.order_type
        price = request.price if request.price is not None else existing_order.price
        amount = request.asset_quantity if request.asset_quantity is not None else existing_order.amount
        time_in_force = request.time_in_force if request.time_in_force is not None else (existing_order.time_in_force or TimeInForce.GTC)
        client_order_id = request.client_order_id if request.client_order_id is not None else existing_order.client_order_id

        # 새 order_id 생성
        new_order_id = f"sim_{uuid.uuid4().hex[:16]}"

        # timestamp (exchange의 현재 시각)
        timestamp = self.exchange.get_current_timestamp()

        # 새 주문 생성
        new_order = SpotOrder(
            order_id=new_order_id,
            stock_address=existing_order.stock_address,
            side=side,
            order_type=order_type,
            price=price,
            amount=amount,
            timestamp=timestamp,
            client_order_id=client_order_id,
            time_in_force=time_in_force,
            min_trade_amount=0.01  # 시뮬레이션 기본값
        )

        return new_order

    def _decode_success(
        self,
        request: ModifyOrReplaceOrderRequest,
        new_order: SpotOrder,
        trades: List[SpotTrade],
        send_when: int,
        receive_when: int
    ) -> ModifyOrReplaceOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        # status 결정
        if trades and len(trades) > 0:
            total_filled = sum(trade.pair.get_asset() for trade in trades)

            if total_filled >= new_order.amount:
                status = OrderStatus.FILLED
            elif total_filled > 0:
                status = OrderStatus.PARTIALLY_FILLED
            else:
                status = OrderStatus.NEW
        else:
            # trades가 비어있으면 미체결
            status = OrderStatus.NEW

        return ModifyOrReplaceOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=new_order.order_id,
            client_order_id=new_order.client_order_id,
            status=status,
            trades=trades if trades else None
        )

    def _decode_error(
        self,
        request: ModifyOrReplaceOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> ModifyOrReplaceOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return ModifyOrReplaceOrderResponse(
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


class TestModifyOrReplaceOrderWorker:
    # ModifyOrReplaceOrderWorker 테스트

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
        # ModifyOrReplaceOrderWorker 생성
        return ModifyOrReplaceOrderWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_modify_pending_order_price(self, worker, exchange, btc_address):
        # 미체결 주문 가격 변경
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. 미체결 LIMIT 주문 생성
        original_order = SpotOrder(
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
        exchange.place_order(original_order)

        # 2. 가격 변경 요청 (즉시 체결 가격으로)
        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=original_order,
            price=current_price  # 즉시 체결
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.order_id is not None
        assert response.order_id != original_order.order_id  # 새 주문 ID
        assert response.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]

    def test_modify_pending_order_quantity(self, worker, exchange, btc_address):
        # 미체결 주문 수량 변경
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. 미체결 LIMIT 주문 생성
        original_order = SpotOrder(
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
        exchange.place_order(original_order)

        # 2. 수량 변경 요청
        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=original_order,
            asset_quantity=0.2  # 수량 변경
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.order_id is not None
        assert response.status == OrderStatus.NEW  # 여전히 미체결

    def test_modify_pending_order_price_and_quantity(self, worker, exchange, btc_address):
        # 미체결 주문 가격+수량 동시 변경
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. 미체결 LIMIT 주문 생성
        original_order = SpotOrder(
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
        exchange.place_order(original_order)

        # 2. 가격+수량 변경 요청
        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=original_order,
            price=current_price,  # 즉시 체결 가격
            asset_quantity=0.05  # 수량 변경
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]

    def test_modify_with_client_order_id(self, worker, exchange, btc_address):
        # client_order_id 변경
        current_price = exchange.get_current_price("BTC/USDT")
        new_client_id = f"modified_{uuid.uuid4().hex[:8]}"

        # 1. 미체결 LIMIT 주문 생성
        original_order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            client_order_id="original_client_id",
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(original_order)

        # 2. client_order_id 변경 요청
        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=original_order,
            client_order_id=new_client_id
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert response.client_order_id == new_client_id

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

        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=fake_order,
            price=46000.0
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
            amount=0.01,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        trades = exchange.place_order(order)

        # 전체 체결 확인
        total_filled = sum(trade.pair.get_asset() for trade in trades)
        if total_filled < 0.01:
            pytest.skip("MARKET order not fully filled in test")

        # 수정 시도
        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=order,
            price=46000.0
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code in ["ORDER_NOT_FOUND", "ORDER_ALREADY_FILLED"]

    def test_invalid_quantity(self, worker, exchange, btc_address):
        # 잘못된 수량 (0)
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. 미체결 LIMIT 주문 생성
        original_order = SpotOrder(
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
        exchange.place_order(original_order)

        # 2. 수량 0으로 변경 시도
        request = ModifyOrReplaceOrderRequest(
            request_id=f"modify_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            original_order=original_order,
            asset_quantity=0.0  # 수량 0
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code == "INVALID_QUANTITY"
