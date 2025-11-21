"""BinanceSpotGateway 실제 API 통합 테스트
XRP 49개 보유 기준으로 실제 거래 테스트
"""
import pytest
import os
import asyncio
from financial_gateway.gateways.binance_spot.BinanceSpotGateway import BinanceSpotGateway
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.structures.create_order import CreateOrderRequest
from financial_gateway.structures.cancel_order import CancelOrderRequest
from financial_gateway.structures.modify_or_replace_order import ModifyOrReplaceOrderRequest
from financial_gateway.structures.see_order import SeeOrderRequest
from financial_gateway.structures.see_open_orders import SeeOpenOrdersRequest
from financial_gateway.structures.see_holdings import SeeHoldingsRequest
from financial_gateway.structures.see_balance import SeeBalanceRequest
from financial_gateway.structures.see_ticker import SeeTickerRequest
from financial_gateway.structures.see_orderbook import SeeOrderbookRequest
from financial_gateway.structures.see_server_time import SeeServerTimeRequest
from financial_assets.stock_address import StockAddress
from financial_assets.order.spot_order import SpotOrder
from financial_assets.symbol import Symbol
from financial_assets.constants import OrderType, OrderSide, TimeInForce, OrderStatus


# API 키 설정 (환경변수에서 로드)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# API 키가 없으면 테스트 스킵
pytestmark = pytest.mark.skipif(
    not BINANCE_API_KEY or not BINANCE_API_SECRET,
    reason="Binance API keys not set. Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables."
)


@pytest.fixture(scope="module")
def throttler():
    """실제 BinanceSpotThrottler 생성"""
    return BinanceSpotThrottler(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)


@pytest.fixture(scope="module")
def gateway(throttler):
    """실제 BinanceSpotGateway 생성"""
    return BinanceSpotGateway(throttler)


@pytest.fixture(scope="module")
def xrp_usdt_address():
    """XRP/USDT StockAddress"""
    return StockAddress("crypto", "BINANCE", "SPOT", "XRP", "USDT", "1d")


# 공유 상태 (테스트 간 데이터 전달)
class TestState:
    current_price = None
    sell_limit_order_id = None
    buy_limit_order_id = None
    usdt_received = None


@pytest.mark.asyncio
class TestPhase1ReadOnly:
    """Phase 1: 읽기 전용 테스트 (안전)"""

    async def test_01_server_time(self, gateway):
        """1-1. 서버 시간 조회"""
        request = SeeServerTimeRequest(
            request_id="test_server_time_001",
            gateway_name="binance_spot"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.server_time > 0
        print(f"\n✅ 서버 시간: {response.server_time}")

    async def test_02_ticker(self, gateway, xrp_usdt_address):
        """1-2. XRP/USDT 시세 조회"""
        request = SeeTickerRequest(
            request_id="test_ticker_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.current > 0

        TestState.current_price = response.current

        print(f"\n✅ XRP/USDT 시세")
        print(f"   현재가: {response.current} USDT")
        print(f"   24h 고가: {response.high} USDT")
        print(f"   24h 저가: {response.low} USDT")
        print(f"   24h 거래량: {response.volume} XRP")

    async def test_03_orderbook(self, gateway, xrp_usdt_address):
        """1-3. 호가창 조회"""
        request = SeeOrderbookRequest(
            request_id="test_orderbook_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            depth=5
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.bids) > 0
        assert len(response.asks) > 0

        print(f"\n✅ 호가창")
        print(f"   매수 1호가: {response.bids[0][0]} USDT ({response.bids[0][1]} XRP)")
        print(f"   매도 1호가: {response.asks[0][0]} USDT ({response.asks[0][1]} XRP)")

    async def test_04_holdings(self, gateway):
        """1-4. XRP 보유량 및 평단가 조회"""
        request = SeeHoldingsRequest(
            request_id="test_holdings_001",
            gateway_name="binance_spot",
            symbols=[Symbol("XRP/USDT")]
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        xrp_holding = response.holdings.get("XRP")
        if xrp_holding:
            total = xrp_holding['balance'].asset.amount
            avg_price = xrp_holding['balance'].value.amount / total if total > 0 else 0

            print(f"\n✅ XRP 보유 정보")
            print(f"   총 보유: {total} XRP")
            print(f"   평단가: {avg_price:.4f} USDT")
            print(f"   거래 가능: {xrp_holding['available']} XRP")
            print(f"   주문 묶임: {xrp_holding['promised']} XRP")
        else:
            print(f"\n⚠️  XRP 보유량이 없거나 너무 적음")

    async def test_05_balance(self, gateway):
        """1-5. USDT 잔고 조회"""
        request = SeeBalanceRequest(
            request_id="test_balance_001",
            gateway_name="binance_spot",
            currencies=["USDT"]
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        usdt_balance = response.balances.get("USDT")
        if usdt_balance:
            print(f"\n✅ USDT 잔고")
            print(f"   총 잔고: {usdt_balance['balance'].amount} USDT")
            print(f"   거래 가능: {usdt_balance['available']} USDT")
        else:
            print(f"\n⚠️  USDT 잔고 없음")


@pytest.mark.asyncio
class TestPhase2SellOrders:
    """Phase 2: 매도 주문 테스트"""

    async def test_10_create_limit_sell_order(self, gateway, xrp_usdt_address):
        """2-1. LIMIT 매도 주문 생성 (현재가 +10%, 즉시 체결 안 됨)"""
        assert TestState.current_price is not None, "Phase 1의 test_02_ticker를 먼저 실행해야 합니다"

        sell_price = round(TestState.current_price * 1.10, 4)

        order = SpotOrder(
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=3.0,
            price=sell_price,
            time_in_force=TimeInForce.GTC,
            client_order_id="test_xrp_sell_limit_001"
        )

        request = CreateOrderRequest(
            request_id="test_create_sell_limit_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.PENDING

        TestState.sell_limit_order_id = response.order_id

        print(f"\n✅ LIMIT 매도 주문 생성")
        print(f"   주문 ID: {response.order_id}")
        print(f"   가격: {sell_price} USDT (현재가 +10%)")
        print(f"   수량: 3 XRP")
        print(f"   상태: {response.status}")

    async def test_11_query_sell_order(self, gateway, xrp_usdt_address):
        """2-2. LIMIT 매도 주문 조회"""
        assert TestState.sell_limit_order_id is not None

        request = SeeOrderRequest(
            request_id="test_see_sell_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order_id=TestState.sell_limit_order_id
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n✅ LIMIT 매도 주문 상태")
        print(f"   상태: {response.order.status}")
        print(f"   체결: {response.filled_amount}/{response.order.quantity} XRP")

    async def test_12_cancel_sell_order(self, gateway, xrp_usdt_address):
        """2-3. LIMIT 매도 주문 취소"""
        assert TestState.sell_limit_order_id is not None

        request = CancelOrderRequest(
            request_id="test_cancel_sell_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order_id=TestState.sell_limit_order_id,
            client_order_id="test_xrp_sell_limit_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.CANCELLED

        print(f"\n✅ LIMIT 매도 주문 취소")
        print(f"   주문 ID: {response.order_id}")
        print(f"   취소 수량: {response.remaining_amount} XRP")

    @pytest.mark.skipif(True, reason="실제 체결됨! 실행하려면 @pytest.mark.skipif(False, ...) 로 변경")
    async def test_13_market_sell_order(self, gateway, xrp_usdt_address):
        """2-4. MARKET 매도 (실제 체결!) - 기본적으로 스킵됨"""
        order = SpotOrder(
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=2.0,
            client_order_id="test_xrp_sell_market_001"
        )

        request = CreateOrderRequest(
            request_id="test_market_sell_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.FILLED

        total_usdt = sum(fill.price * fill.quantity for fill in response.fills)
        TestState.usdt_received = total_usdt

        print(f"\n💰 MARKET 매도 체결")
        print(f"   체결량: {response.filled_amount} XRP")
        print(f"   총 획득 USDT: {total_usdt:.4f}")
        print(f"   평균 체결가: {total_usdt / response.filled_amount:.4f} USDT")


@pytest.mark.asyncio
class TestPhase3BuyOrders:
    """Phase 3: 매수 주문 테스트"""

    async def test_20_create_limit_buy_order(self, gateway, xrp_usdt_address):
        """3-1. LIMIT 매수 주문 생성 (현재가 -10%, 즉시 체결 안 됨)"""
        assert TestState.current_price is not None

        buy_price = round(TestState.current_price * 0.90, 4)

        order = SpotOrder(
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=2.0,
            price=buy_price,
            time_in_force=TimeInForce.GTC,
            client_order_id="test_xrp_buy_limit_001"
        )

        request = CreateOrderRequest(
            request_id="test_create_buy_limit_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.PENDING

        TestState.buy_limit_order_id = response.order_id

        print(f"\n✅ LIMIT 매수 주문 생성")
        print(f"   주문 ID: {response.order_id}")
        print(f"   가격: {buy_price} USDT (현재가 -10%)")
        print(f"   수량: 2 XRP")
        print(f"   예상 사용: {buy_price * 2:.4f} USDT")

    async def test_21_modify_buy_order(self, gateway, xrp_usdt_address):
        """3-2. LIMIT 매수 주문 수정 (가격 변경)"""
        assert TestState.buy_limit_order_id is not None
        assert TestState.current_price is not None

        new_price = round(TestState.current_price * 0.85, 4)

        original_order = SpotOrder(
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=2.0,
            price=round(TestState.current_price * 0.90, 4),
            order_id=TestState.buy_limit_order_id,
            client_order_id="test_xrp_buy_limit_001"
        )

        request = ModifyOrReplaceOrderRequest(
            request_id="test_modify_buy_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            original_order=original_order,
            new_price=new_price,
            new_client_order_id="test_xrp_buy_limit_001_modified"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        TestState.buy_limit_order_id = response.new_order_id

        print(f"\n✅ LIMIT 매수 주문 수정")
        print(f"   기존 주문 취소: {response.old_order_id}")
        print(f"   새 주문 생성: {response.new_order_id}")
        print(f"   새 가격: {new_price} USDT (현재가 -15%)")

    async def test_22_cancel_buy_order(self, gateway, xrp_usdt_address):
        """3-3. LIMIT 매수 주문 취소"""
        assert TestState.buy_limit_order_id is not None

        request = CancelOrderRequest(
            request_id="test_cancel_buy_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order_id=TestState.buy_limit_order_id,
            client_order_id="test_xrp_buy_limit_001_modified"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.CANCELLED

        print(f"\n✅ LIMIT 매수 주문 취소")
        print(f"   주문 ID: {response.order_id}")
        print(f"   취소 수량: {response.remaining_amount} XRP")

    @pytest.mark.skipif(True, reason="실제 체결됨! 실행하려면 @pytest.mark.skipif(False, ...) 로 변경")
    async def test_23_market_buy_order(self, gateway, xrp_usdt_address):
        """3-4. MARKET 매수 (실제 체결!) - 기본적으로 스킵됨"""
        order = SpotOrder(
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.9,
            client_order_id="test_xrp_buy_market_001"
        )

        request = CreateOrderRequest(
            request_id="test_market_buy_001",
            gateway_name="binance_spot",
            address=xrp_usdt_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.FILLED

        total_usdt = sum(fill.price * fill.quantity for fill in response.fills)

        print(f"\n💰 MARKET 매수 체결")
        print(f"   체결량: {response.filled_amount} XRP")
        print(f"   총 사용 USDT: {total_usdt:.4f}")
        print(f"   평균 체결가: {total_usdt / response.filled_amount:.4f} USDT")


@pytest.mark.asyncio
class TestPhase4Verification:
    """Phase 4: 최종 검증"""

    async def test_30_open_orders(self, gateway, xrp_usdt_address):
        """4-1. 미체결 주문 목록 확인 (모두 취소되었는지)"""
        request = SeeOpenOrdersRequest(
            request_id="test_open_orders_final",
            gateway_name="binance_spot",
            address=xrp_usdt_address
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n✅ 미체결 주문 목록")
        print(f"   개수: {len(response.orders)}")

        if response.orders:
            for order in response.orders:
                print(f"   - {order.order_id}: {order.side} {order.quantity} @ {order.price}")

    async def test_31_final_holdings(self, gateway):
        """4-2. 최종 XRP 보유량 확인"""
        request = SeeHoldingsRequest(
            request_id="test_holdings_final",
            gateway_name="binance_spot",
            symbols=[Symbol("XRP/USDT")]
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        xrp_holding = response.holdings.get("XRP")
        if xrp_holding:
            total = xrp_holding['balance'].asset.amount

            print(f"\n📦 최종 XRP 보유량")
            print(f"   총 보유: {total} XRP")
            print(f"   거래 가능: {xrp_holding['available']} XRP")

    async def test_32_final_balance(self, gateway):
        """4-3. 최종 USDT 잔고 확인"""
        request = SeeBalanceRequest(
            request_id="test_balance_final",
            gateway_name="binance_spot",
            currencies=["USDT"]
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        usdt_balance = response.balances.get("USDT")
        if usdt_balance:
            print(f"\n💵 최종 USDT 잔고")
            print(f"   총 잔고: {usdt_balance['balance'].amount} USDT")
            print(f"   거래 가능: {usdt_balance['available']} USDT")
