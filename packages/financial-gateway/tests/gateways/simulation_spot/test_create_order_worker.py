"""CreateOrderWorker TDD 테스트"""

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
class CreateOrderRequest(BaseRequest):
    address: StockAddress
    side: OrderSide
    order_type: OrderType
    asset_quantity: Optional[float] = None
    price: Optional[float] = None
    quote_quantity: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Optional[TimeInForce] = None
    post_only: bool = False
    client_order_id: Optional[str] = None


@dataclass
class CreateOrderResponse(BaseResponse):
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    created_at: Optional[int] = None
    trades: Optional[List[SpotTrade]] = None


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class CreateOrderWorker:
    # 주문 생성 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: CreateOrderRequest) -> CreateOrderResponse:
        # 주문 생성 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. Encode: Request → SpotOrder
            order = self._encode(request)

            # 2. Exchange 호출
            trades = self.exchange.place_order(order)
            receive_when = self._get_timestamp_ms()

            # 3. Decode: trades → Response
            return self._decode_success(request, order, trades, send_when, receive_when)

        except ValueError as e:
            # 잔고 부족, 잘못된 수량 등
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

        except KeyError as e:
            # 잘못된 심볼
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "INVALID_SYMBOL", str(e), send_when, receive_when)

        except Exception as e:
            # 기타 에러
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _encode(self, request: CreateOrderRequest) -> SpotOrder:
        # Request → SpotOrder 변환
        # client_order_id 결정 (없으면 request_id 사용)
        client_order_id = request.client_order_id if request.client_order_id else request.request_id

        # order_id 생성 (UUID)
        order_id = f"sim_{uuid.uuid4().hex[:16]}"

        # timestamp (exchange의 현재 시각, 초 단위)
        timestamp = self.exchange.get_current_timestamp()

        # time_in_force 기본값 처리
        time_in_force = request.time_in_force if request.time_in_force else TimeInForce.GTC

        # SpotOrder 생성
        order = SpotOrder(
            order_id=order_id,
            stock_address=request.address,
            side=request.side,
            order_type=request.order_type,
            price=request.price,
            amount=request.asset_quantity,
            timestamp=timestamp,
            client_order_id=client_order_id,
            time_in_force=time_in_force,
            min_trade_amount=0.01  # 시뮬레이션 기본값
        )

        return order

    def _decode_success(
        self,
        request: CreateOrderRequest,
        order: SpotOrder,
        trades: List[SpotTrade],
        send_when: int,
        receive_when: int
    ) -> CreateOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        # status 결정
        if trades and len(trades) > 0:
            total_filled = sum(trade.pair.get_asset() for trade in trades)

            if total_filled >= order.amount:
                status = OrderStatus.FILLED
            elif total_filled > 0:
                status = OrderStatus.PARTIALLY_FILLED
            else:
                status = OrderStatus.NEW
        else:
            # trades가 비어있으면 미체결
            status = OrderStatus.NEW

        return CreateOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order.order_id,
            client_order_id=order.client_order_id,
            status=status,
            created_at=processed_when,
            trades=trades if trades else None
        )

    def _decode_error(
        self,
        request: CreateOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> CreateOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return CreateOrderResponse(
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


class TestCreateOrderWorker:
    """CreateOrderWorker 테스트"""

    @pytest.fixture
    def market_data(self):
        """테스트용 MarketData 생성"""
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

        # MarketData 생성 (offset 10)
        return MarketData(mc, start_offset=10)

    @pytest.fixture
    def exchange(self, market_data):
        """테스트용 SpotExchange 생성"""
        return SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

    @pytest.fixture
    def worker(self, exchange):
        """CreateOrderWorker 생성"""
        return CreateOrderWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        """BTC/USDT StockAddress"""
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    @pytest.fixture
    def eth_address(self):
        """ETH/USDT StockAddress"""
        return StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_limit_order_full_fill(self, worker, exchange, btc_address):
        """LIMIT 주문 완전 체결 (현재가 매수)"""
        current_price = exchange.get_current_price("BTC/USDT")

        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            asset_quantity=0.1,
            price=current_price,  # 현재가 = 즉시 체결
            time_in_force=None  # GTC 기본값
        )

        response = worker.execute(request)

        assert response.is_success is True
        assert response.request_id == request.request_id
        assert response.status == OrderStatus.FILLED
        assert response.order_id is not None
        assert response.client_order_id == request.request_id  # request_id 사용
        assert response.trades is not None
        assert len(response.trades) > 0
        assert response.created_at is not None
        assert response.send_when > 0
        assert response.receive_when > 0
        assert response.processed_when > 0
        assert response.timegaps >= 0

        # 체결량 확인
        total_filled = sum(trade.pair.get_asset() for trade in response.trades)
        assert total_filled == 0.1

    def test_limit_order_partial_fill(self, worker, exchange, btc_address):
        """LIMIT 주문 부분 체결"""
        # 시뮬레이션에서는 LIMIT 주문이 항상 전량 체결되므로
        # 이 테스트는 실제로는 전량 체결될 것
        # OrderBook에 남는 것은 가격이 맞지 않을 때만 발생
        current_price = exchange.get_current_price("BTC/USDT")

        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            asset_quantity=0.5,
            price=current_price * 1.01,  # 약간 높은 가격 (즉시 체결 가능)
        )

        response = worker.execute(request)

        assert response.is_success is True
        assert response.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED, OrderStatus.NEW]

    def test_limit_order_no_fill(self, worker, exchange, btc_address):
        """LIMIT 주문 미체결 (낮은 가격)"""
        current_price = exchange.get_current_price("BTC/USDT")

        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            asset_quantity=0.1,
            price=current_price * 0.5,  # 현재가의 절반 = 미체결
        )

        response = worker.execute(request)

        assert response.is_success is True
        assert response.status == OrderStatus.NEW
        assert response.trades is None or len(response.trades) == 0

    def test_market_order_buy(self, worker, exchange, btc_address):
        """MARKET 주문 매수 (즉시 체결)"""
        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=0.1,
        )

        response = worker.execute(request)

        assert response.is_success is True
        # MARKET 주문은 FILLED 또는 PARTIALLY_FILLED 가능
        assert response.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]
        assert response.trades is not None
        assert len(response.trades) > 0

        # 체결량 확인 (부분 체결 가능)
        total_filled = sum(trade.pair.get_asset() for trade in response.trades)
        assert total_filled > 0
        assert total_filled <= 0.1

    def test_market_order_sell(self, worker, exchange, btc_address):
        """MARKET 주문 매도"""
        # 먼저 매수하여 보유량 확보
        buy_order_request = CreateOrderRequest(
            request_id=f"buy_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=0.2,
        )
        buy_response = worker.execute(buy_order_request)
        assert buy_response.is_success is True

        # 매도 주문
        sell_request = CreateOrderRequest(
            request_id=f"sell_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            asset_quantity=0.1,
        )

        response = worker.execute(sell_request)

        assert response.is_success is True
        # MARKET 주문은 FILLED 또는 PARTIALLY_FILLED 가능
        assert response.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]
        assert response.trades is not None
        assert len(response.trades) > 0

    def test_client_order_id(self, worker, exchange, btc_address):
        """client_order_id 지정"""
        client_id = f"my_order_{uuid.uuid4().hex[:8]}"

        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=0.05,
            client_order_id=client_id
        )

        response = worker.execute(request)

        assert response.is_success is True
        assert response.client_order_id == client_id

    # ========== 실패 케이스 ==========

    def test_insufficient_balance(self, worker, exchange, btc_address):
        """잔고 부족"""
        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=1000.0,  # 매우 큰 수량
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code == "INSUFFICIENT_BALANCE"
        assert response.error_message is not None

    def test_invalid_symbol(self, worker, exchange):
        """잘못된 심볼"""
        invalid_address = StockAddress("candle", "binance", "spot", "INVALID", "USDT", "1m")

        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=invalid_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=0.1,
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code == "INVALID_SYMBOL"

    def test_invalid_quantity(self, worker, exchange, btc_address):
        """잘못된 수량 (0 또는 음수)"""
        request = CreateOrderRequest(
            request_id=f"test_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=0.0,  # 수량 0
        )

        response = worker.execute(request)

        assert response.is_success is False
        assert response.error_code == "INVALID_QUANTITY"

    # ========== 인코딩/디코딩 테스트 ==========

    def test_encode_request(self, worker, btc_address):
        """CreateOrderRequest → SpotOrder 변환"""
        request = CreateOrderRequest(
            request_id="encode_test_001",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            asset_quantity=0.1,
            price=45000.0,
            client_order_id="my_order_123"
        )

        # _encode 메서드 직접 테스트
        order = worker._encode(request)

        assert order.stock_address.to_symbol().to_slash() == "BTC/USDT"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.LIMIT
        assert order.amount == 0.1
        assert order.price == 45000.0
        assert order.client_order_id == "my_order_123"
        assert order.timestamp > 0

    def test_decode_trades(self, worker, exchange, btc_address):
        """list[SpotTrade] → CreateOrderResponse 변환"""
        request = CreateOrderRequest(
            request_id="decode_test_001",
            gateway_name="simulation",
            address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            asset_quantity=0.1,
        )

        response = worker.execute(request)

        # trades가 있을 때
        assert response.is_success is True
        assert response.trades is not None

        # status 결정 로직 확인
        total_filled = sum(trade.pair.get_asset() for trade in response.trades)
        if total_filled >= 0.1:
            assert response.status == OrderStatus.FILLED
        elif total_filled > 0:
            assert response.status == OrderStatus.PARTIALLY_FILLED
        else:
            assert response.status == OrderStatus.NEW
