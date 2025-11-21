"""UpbitSpotGateway 실제 API 통합 테스트
보유 자산 기준으로 실제 거래 테스트
"""
import pytest
import os
import asyncio
from financial_gateway.gateways.upbit_spot.UpbitSpotGateway import UpbitSpotGateway
from throttled_api.providers.upbit import UpbitSpotThrottler
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
from financial_gateway.structures.see_available_markets import SeeAvailableMarketsRequest
from financial_assets.stock_address import StockAddress
from financial_assets.order.spot_order import SpotOrder
from financial_assets.symbol import Symbol
from financial_assets.constants import OrderType, OrderSide, TimeInForce, OrderStatus


# API 키 설정 (환경변수에서 로드)
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

# API 키가 없으면 테스트 스킵
pytestmark = pytest.mark.skipif(
    not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY,
    reason="Upbit API keys not set. Set UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY environment variables."
)


@pytest.fixture(scope="module")
def throttler():
    """실제 UpbitSpotThrottler 생성"""
    return UpbitSpotThrottler(
        access_key=UPBIT_ACCESS_KEY,
        secret_key=UPBIT_SECRET_KEY
    )


@pytest.fixture(scope="module")
def gateway(throttler):
    """실제 UpbitSpotGateway 생성"""
    return UpbitSpotGateway(throttler)


@pytest.fixture(scope="module")
def xrp_krw_address():
    """XRP/KRW StockAddress"""
    return StockAddress("crypto", "UPBIT", "SPOT", "XRP", "KRW", "1d")


# 공유 상태 (테스트 간 데이터 전달)
class TestState:
    current_price = None
    best_bid = None  # 매수 1호가 (내가 팔 수 있는 가격)
    best_ask = None  # 매도 1호가 (내가 살 수 있는 가격)
    sell_limit_order_id = None
    buy_limit_order_id = None


@pytest.mark.asyncio
class TestPhase1ReadOnly:
    """Phase 1: 읽기 전용 테스트 (안전)"""

    async def test_01_server_time(self, gateway):
        """1-1. 서버 시간 조회 (로컬 시간)"""
        request = SeeServerTimeRequest(
            request_id="test_server_time_001",
            gateway_name="upbit_spot"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.server_time > 0
        print(f"\n✅ 서버 시간: {response.server_time}")

    async def test_02_ticker(self, gateway, xrp_krw_address):
        """1-2. XRP/KRW 시세 조회"""
        request = SeeTickerRequest(
            request_id="test_ticker_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.current > 0

        TestState.current_price = response.current

        print(f"\n✅ XRP/KRW 시세")
        print(f"   현재가: {response.current} KRW")
        print(f"   24h 고가: {response.high} KRW")
        print(f"   24h 저가: {response.low} KRW")
        print(f"   24h 거래량: {response.volume} XRP")

    async def test_03_orderbook(self, gateway, xrp_krw_address):
        """1-3. 호가창 조회 (매매 기준가 설정)"""
        request = SeeOrderbookRequest(
            request_id="test_orderbook_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            depth=10
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.bids) > 0
        assert len(response.asks) > 0

        # 호가 정보 저장 (실제 거래에 사용)
        TestState.best_bid = response.bids[0][0]  # 최고 매수 호가
        TestState.best_ask = response.asks[0][0]  # 최저 매도 호가

        print(f"\n✅ 호가창 (XRP/KRW)")
        print(f"   매수 1호가: {TestState.best_bid} KRW (수량: {response.bids[0][1]} XRP)")
        print(f"   매도 1호가: {TestState.best_ask} KRW (수량: {response.asks[0][1]} XRP)")
        print(f"   스프레드: {TestState.best_ask - TestState.best_bid} KRW")

    async def test_04_holdings(self, gateway):
        """1-4. 보유 자산 조회 (평단가 포함)"""
        request = SeeHoldingsRequest(
            request_id="test_holdings_001",
            gateway_name="upbit_spot",
            symbols=None  # 전체 조회
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n✅ 보유 자산 (총 {len(response.holdings)}개)")
        for currency, holding in list(response.holdings.items())[:5]:  # 최대 5개만 출력
            total = holding['balance'].asset.amount
            avg_price = holding['balance'].value.amount / total if total > 0 else 0
            print(f"   {currency}: {total} (평단가: {avg_price:.2f} {holding['balance'].value.symbol})")

    async def test_05_balance(self, gateway):
        """1-5. KRW 잔고 조회"""
        request = SeeBalanceRequest(
            request_id="test_balance_001",
            gateway_name="upbit_spot",
            currencies=["KRW"]
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        krw_balance = response.balances.get("KRW")
        if krw_balance:
            print(f"\n✅ KRW 잔고")
            print(f"   총 잔고: {krw_balance['balance'].amount} KRW")
            print(f"   거래 가능: {krw_balance['available']} KRW")
        else:
            print(f"\n⚠️  KRW 잔고 없음")

    async def test_06_available_markets(self, gateway):
        """1-6. 거래 가능 마켓 조회"""
        request = SeeAvailableMarketsRequest(
            request_id="test_markets_001",
            gateway_name="upbit_spot"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.markets) > 0

        print(f"\n✅ 거래 가능 마켓 (총 {len(response.markets)}개)")
        # KRW 마켓만 필터링
        krw_markets = [m for m in response.markets if m["address"].quote == "KRW"]
        print(f"   KRW 마켓: {len(krw_markets)}개")


@pytest.mark.asyncio
class TestPhase2SellOrders:
    """Phase 2: 매도 주문 테스트"""

    async def test_10_create_limit_sell_order(self, gateway, xrp_krw_address):
        """2-1. LIMIT 매도 주문 생성 (체결 안 될 높은 가격)"""
        assert TestState.best_ask is not None, "Phase 1의 test_03_orderbook을 먼저 실행해야 합니다"

        # 매도 1호가보다 100원 높게 설정 → 절대 체결 안 됨
        sell_price = TestState.best_ask + 100

        order = SpotOrder(
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=5.0,  # XRP 5개
            price=sell_price,
            time_in_force=TimeInForce.GTC,
            client_order_id="test_xrp_sell_limit_001"
        )

        request = CreateOrderRequest(
            request_id="test_create_sell_limit_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.PENDING

        TestState.sell_limit_order_id = response.order_id

        print(f"\n✅ LIMIT 매도 주문 생성")
        print(f"   주문 ID: {response.order_id}")
        print(f"   가격: {sell_price} KRW (매도1호가 {TestState.best_ask} + 100원)")
        print(f"   수량: 5 XRP")
        print(f"   상태: {response.status}")

    async def test_11_query_sell_order(self, gateway, xrp_krw_address):
        """2-2. LIMIT 매도 주문 조회"""
        assert TestState.sell_limit_order_id is not None

        request = SeeOrderRequest(
            request_id="test_see_sell_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order_id=TestState.sell_limit_order_id
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n✅ LIMIT 매도 주문 상태")
        print(f"   상태: {response.order.status}")
        print(f"   체결: {response.filled_amount}/{response.order.quantity} XRP")

    async def test_12_cancel_sell_order(self, gateway, xrp_krw_address):
        """2-3. LIMIT 매도 주문 취소"""
        assert TestState.sell_limit_order_id is not None

        request = CancelOrderRequest(
            request_id="test_cancel_sell_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order_id=TestState.sell_limit_order_id,
            client_order_id="test_xrp_sell_limit_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.CANCELLED

        print(f"\n✅ LIMIT 매도 주문 취소")
        print(f"   주문 ID: {response.order_id}")
        print(f"   취소 수량: {response.remaining_amount} XRP")

    async def test_13_market_sell_order(self, gateway, xrp_krw_address):
        """2-4. MARKET 매도 (실제 체결!)"""
        # Upbit MARKET 매도: quantity에 매도할 수량(XRP) 지정
        order = SpotOrder(
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=5.0,  # 매도 수량: XRP 5개
            client_order_id="test_xrp_sell_market_001"
        )

        request = CreateOrderRequest(
            request_id="test_market_sell_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n💰 MARKET 매도 체결")
        print(f"   체결량: {response.filled_amount} XRP")
        print(f"   주문 ID: {response.order_id}")


@pytest.mark.asyncio
class TestPhase3BuyOrders:
    """Phase 3: 매수 주문 테스트"""

    async def test_20_create_limit_buy_order(self, gateway, xrp_krw_address):
        """3-1. LIMIT 매수 주문 생성 (체결 안 될 낮은 가격)"""
        assert TestState.best_bid is not None, "Phase 1의 test_03_orderbook을 먼저 실행해야 합니다"

        # 매수 1호가보다 100원 낮게 설정 → 절대 체결 안 됨
        buy_price = TestState.best_bid - 100

        order = SpotOrder(
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=5.0,  # XRP 5개
            price=buy_price,
            time_in_force=TimeInForce.GTC,
            client_order_id="test_xrp_buy_limit_001"
        )

        request = CreateOrderRequest(
            request_id="test_create_buy_limit_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.PENDING

        TestState.buy_limit_order_id = response.order_id

        print(f"\n✅ LIMIT 매수 주문 생성")
        print(f"   주문 ID: {response.order_id}")
        print(f"   가격: {buy_price} KRW (매수1호가 {TestState.best_bid} - 100원)")
        print(f"   수량: 5 XRP")
        print(f"   예상 사용: {buy_price * 5} KRW")

    async def test_21_modify_buy_order(self, gateway, xrp_krw_address):
        """3-2. LIMIT 매수 주문 수정 (가격 더 낮게)"""
        assert TestState.buy_limit_order_id is not None
        assert TestState.best_bid is not None

        original_price = TestState.best_bid - 100
        new_price = TestState.best_bid - 200  # 더 낮게 수정

        original_order = SpotOrder(
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=5.0,
            price=original_price,
            order_id=TestState.buy_limit_order_id,
            client_order_id="test_xrp_buy_limit_001"
        )

        request = ModifyOrReplaceOrderRequest(
            request_id="test_modify_buy_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            original_order=original_order,
            new_price=new_price,
            new_client_order_id="test_xrp_buy_limit_001_modified"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        TestState.buy_limit_order_id = response.new_order_id

        print(f"\n✅ LIMIT 매수 주문 수정 (Cancel + Create)")
        print(f"   기존 주문 취소: {response.old_order_id}")
        print(f"   새 주문 생성: {response.new_order_id}")
        print(f"   기존 가격: {original_price} KRW (매수1호가 - 100원)")
        print(f"   새 가격: {new_price} KRW (매수1호가 - 200원)")

    async def test_22_cancel_buy_order(self, gateway, xrp_krw_address):
        """3-3. LIMIT 매수 주문 취소"""
        assert TestState.buy_limit_order_id is not None

        request = CancelOrderRequest(
            request_id="test_cancel_buy_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order_id=TestState.buy_limit_order_id,
            client_order_id="test_xrp_buy_limit_001_modified"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == OrderStatus.CANCELLED

        print(f"\n✅ LIMIT 매수 주문 취소")
        print(f"   주문 ID: {response.order_id}")
        print(f"   취소 수량: {response.remaining_amount} XRP")

    async def test_23_market_buy_order(self, gateway, xrp_krw_address):
        """3-4. MARKET 매수 (실제 체결!)"""
        # Upbit MARKET 매수: price에 매수할 금액(KRW) 지정 (수량 아님!)
        buy_amount = 10000  # 매수 금액: 10,000 KRW

        order = SpotOrder(
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=buy_amount,  # 매수 금액: 10,000 KRW (quantity 아님!)
            client_order_id="test_xrp_buy_market_001"
        )

        request = CreateOrderRequest(
            request_id="test_market_buy_001",
            gateway_name="upbit_spot",
            address=xrp_krw_address,
            order=order
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n💰 MARKET 매수 체결")
        print(f"   체결량: {response.filled_amount} XRP")
        print(f"   사용 금액: {buy_amount} KRW")


@pytest.mark.asyncio
class TestPhase4Verification:
    """Phase 4: 최종 검증"""

    async def test_30_open_orders(self, gateway, xrp_krw_address):
        """4-1. 미체결 주문 목록 확인 (모두 취소되었는지)"""
        request = SeeOpenOrdersRequest(
            request_id="test_open_orders_final",
            gateway_name="upbit_spot",
            address=xrp_krw_address
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n✅ 미체결 주문 목록")
        print(f"   개수: {len(response.orders)}")

        if response.orders:
            for order in response.orders:
                print(f"   - {order.order_id}: {order.side} {order.quantity} @ {order.price}")

    async def test_31_final_holdings(self, gateway):
        """4-2. 최종 보유량 확인"""
        request = SeeHoldingsRequest(
            request_id="test_holdings_final",
            gateway_name="upbit_spot",
            symbols=[Symbol("XRP/KRW")]
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
        """4-3. 최종 KRW 잔고 확인"""
        request = SeeBalanceRequest(
            request_id="test_balance_final",
            gateway_name="upbit_spot",
            currencies=["KRW"]
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        krw_balance = response.balances.get("KRW")
        if krw_balance:
            print(f"\n💵 최종 KRW 잔고")
            print(f"   총 잔고: {krw_balance['balance'].amount} KRW")
            print(f"   거래 가능: {krw_balance['available']} KRW")
