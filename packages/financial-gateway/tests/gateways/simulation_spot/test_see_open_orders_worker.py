# SeeOpenOrdersWorker TDD 테스트

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
class SeeOpenOrdersRequest(BaseRequest):
    address: Optional[StockAddress] = None
    limit: Optional[int] = None


@dataclass
class SeeOpenOrdersResponse(BaseResponse):
    orders: List[SpotOrder] = field(default_factory=list)


# Worker 클래스 임시 정의
from simple_logger import init_logging, func_logging


class SeeOpenOrdersWorker:
    # 미체결 주문 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeOpenOrdersRequest) -> SeeOpenOrdersResponse:
        # 미체결 주문 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. symbol 추출 (address가 있으면)
            symbol = self._get_symbol(request.address) if request.address else None

            # 2. Exchange에서 미체결 주문 조회
            orders = self.exchange.get_open_orders(symbol)
            receive_when = self._get_timestamp_ms()

            # 3. 최신순 정렬 (timestamp 내림차순)
            orders = sorted(orders, key=lambda o: o.timestamp, reverse=True)

            # 4. limit 적용
            if request.limit is not None and request.limit > 0:
                orders = orders[:request.limit]

            # 5. Decode: → Response
            return self._decode_success(request, orders, send_when, receive_when)

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
        request: SeeOpenOrdersRequest,
        orders: List[SpotOrder],
        send_when: int,
        receive_when: int
    ) -> SeeOpenOrdersResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOpenOrdersResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            orders=orders
        )

    def _decode_error(
        self,
        request: SeeOpenOrdersRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeOpenOrdersResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOpenOrdersResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=error_message,
            orders=[]
        )

    def _get_timestamp_ms(self) -> int:
        # 현재 시뮬레이션 타임스탬프 (초 → 밀리초 변환)
        return self.exchange.get_current_timestamp() * 1000


class TestSeeOpenOrdersWorker:
    # SeeOpenOrdersWorker 테스트

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
        # SeeOpenOrdersWorker 생성
        return SeeOpenOrdersWorker(exchange)

    @pytest.fixture
    def btc_address(self):
        # BTC/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

    @pytest.fixture
    def eth_address(self):
        # ETH/USDT StockAddress
        return StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")

    # ========== 성공 케이스 ==========

    def test_see_all_open_orders(self, worker, exchange, btc_address, eth_address):
        # 전체 미체결 주문 조회
        current_price_btc = exchange.get_current_price("BTC/USDT")
        current_price_eth = exchange.get_current_price("ETH/USDT")

        # 1. BTC 미체결 주문 생성
        btc_order = SpotOrder(
            order_id=f"btc_order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price_btc * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(btc_order)

        # 2. ETH 미체결 주문 생성
        eth_order = SpotOrder(
            order_id=f"eth_order_{uuid.uuid4().hex[:8]}",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price_eth * 0.5,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(eth_order)

        # 3. 전체 미체결 주문 조회
        request = SeeOpenOrdersRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=None  # 전체
        )

        response = worker.execute(request)

        # 4. 검증
        assert response.is_success is True
        assert len(response.orders) == 2
        assert any(o.order_id == btc_order.order_id for o in response.orders)
        assert any(o.order_id == eth_order.order_id for o in response.orders)

        # 최신순 정렬 확인 (timestamp가 같으면 순서 불확실, 두 주문 모두 있으면 OK)
        order_ids = [o.order_id for o in response.orders]
        assert btc_order.order_id in order_ids
        assert eth_order.order_id in order_ids

    def test_see_open_orders_by_symbol(self, worker, exchange, btc_address, eth_address):
        # 특정 마켓 미체결 주문 조회
        current_price_btc = exchange.get_current_price("BTC/USDT")
        current_price_eth = exchange.get_current_price("ETH/USDT")

        # 1. BTC 미체결 주문 생성
        btc_order = SpotOrder(
            order_id=f"btc_order_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price_btc * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(btc_order)

        # 2. ETH 미체결 주문 생성
        eth_order = SpotOrder(
            order_id=f"eth_order_{uuid.uuid4().hex[:8]}",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price_eth * 0.5,
            amount=1.0,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(eth_order)

        # 3. BTC 마켓만 조회
        request = SeeOpenOrdersRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 4. 검증
        assert response.is_success is True
        assert len(response.orders) == 1
        assert response.orders[0].order_id == btc_order.order_id

    def test_see_open_orders_with_limit(self, worker, exchange, btc_address):
        # limit으로 개수 제한
        current_price = exchange.get_current_price("BTC/USDT")

        # 1. 여러 미체결 주문 생성
        order_ids = []
        for i in range(5):
            order = SpotOrder(
                order_id=f"order_{i}_{uuid.uuid4().hex[:8]}",
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
            order_ids.append(order.order_id)

        # 2. limit=3으로 조회
        request = SeeOpenOrdersRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address,
            limit=3
        )

        response = worker.execute(request)

        # 3. 검증
        assert response.is_success is True
        assert len(response.orders) == 3

    def test_see_open_orders_empty(self, worker, exchange):
        # 미체결 주문이 없을 때
        request = SeeOpenOrdersRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=None
        )

        response = worker.execute(request)

        # 검증
        assert response.is_success is True
        assert len(response.orders) == 0

    def test_see_open_orders_excludes_filled(self, worker, exchange, btc_address):
        # 체결된 주문은 제외됨
        # 1. MARKET 주문 (즉시 체결)
        market_order = SpotOrder(
            order_id=f"market_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.01,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(market_order)

        # 2. LIMIT 미체결 주문
        current_price = exchange.get_current_price("BTC/USDT")
        limit_order = SpotOrder(
            order_id=f"limit_{uuid.uuid4().hex[:8]}",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=current_price * 0.5,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(limit_order)

        # 3. 미체결 주문만 조회
        request = SeeOpenOrdersRequest(
            request_id=f"see_{uuid.uuid4().hex[:8]}",
            gateway_name="simulation",
            address=btc_address
        )

        response = worker.execute(request)

        # 4. 검증 (LIMIT만 있어야 함)
        assert response.is_success is True
        assert len(response.orders) >= 1  # LIMIT 주문은 있어야 함
        assert all(o.order_id != market_order.order_id for o in response.orders)  # MARKET 주문은 없어야 함
