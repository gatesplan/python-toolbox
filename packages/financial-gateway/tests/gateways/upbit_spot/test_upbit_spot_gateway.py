"""UpbitSpotGateway 실제 API 통합 테스트
GatewayService + RequestFactory 사용
"""
import pytest
import financial_gateway as fg


@pytest.fixture(scope="module")
def service():
    """GatewayService 생성 (환경변수에서 로드)"""
    return fg.GatewayService.from_env()


@pytest.fixture(scope="module")
def gateway(service):
    """Upbit Spot Gateway 획득"""
    try:
        return service.get('upbit_spot')
    except ValueError as e:
        pytest.skip(f"Upbit gateway not configured: {e}")


@pytest.fixture(scope="module")
def factory():
    """RequestFactory 생성"""
    return fg.RequestFactory("upbit_spot")


@pytest.fixture(scope="module")
def xrp_krw_address():
    """XRP/KRW StockAddress"""
    return fg.StockAddress("crypto", "UPBIT", "SPOT", "XRP", "KRW", "1d")


# 공유 상태 (테스트 간 데이터 전달)
class TestState:
    # 초기 상태
    initial_krw_balance = None
    initial_xrp_holdings = None

    # 최종 상태
    final_krw_balance = None
    final_xrp_holdings = None

    # 시세 정보
    current_price = None

    # 주문 객체
    limit_sell_order = None
    limit_buy_order = None

    # 주문 ID
    market_buy_order_id = None
    market_buy_client_order_id = None
    market_sell_order_id = None
    market_sell_client_order_id = None

    # 거래 내역
    buy_trades = None
    sell_trades = None


@pytest.mark.asyncio
class TestPhase1InitialState:
    """Phase 1: 조회 및 초기 상태 확인"""

    async def test_01_server_time(self, gateway, factory):
        """1-1. 서버 시간 조회"""
        request = factory.see_server_time(
            request_id="test_server_time_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.server_time > 0
        print(f"\n[OK] Server time: {response.server_time}")

    async def test_02_available_markets(self, gateway, factory):
        """1-2. 거래 가능 마켓 목록"""
        request = factory.see_available_markets(
            request_id="test_markets_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.markets) > 0

        # XRP/KRW 마켓 존재 확인
        xrp_krw_markets = [m for m in response.markets
                           if m.symbol.base == "XRP" and m.symbol.quote == "KRW"]

        print(f"\n[OK] Available Markets")
        print(f"   Total: {len(response.markets)}")
        print(f"   XRP/KRW: {len(xrp_krw_markets)}")
        if xrp_krw_markets:
            market = xrp_krw_markets[0]
            print(f"   Status: {market.status}")
            print(f"   Min Trade Value: {market.min_trade_value_size} KRW")
            print(f"   Min Trade Asset: {market.min_trade_asset_size} XRP")
            print(f"   Value Tick: {market.min_value_tick_size} (가격대별)")
            print(f"   Asset Tick: {market.min_asset_tick_size} XRP")
        assert len(xrp_krw_markets) > 0, "XRP/KRW market not found"

    async def test_03_ticker(self, gateway, factory, xrp_krw_address):
        """1-3. XRP/KRW 시세 조회"""
        request = factory.see_ticker(
            address=xrp_krw_address,
            request_id="test_ticker_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.current > 0

        TestState.current_price = response.current

        print(f"\n[OK] XRP/KRW Ticker")
        print(f"   Current: KRW {response.current:.2f}")
        print(f"   24h High: KRW {response.high:.2f}")
        print(f"   24h Low: KRW {response.low:.2f}")
        print(f"   24h Volume: {response.volume:.2f} XRP")

    async def test_04_orderbook(self, gateway, factory, xrp_krw_address):
        """1-4. 호가창 조회"""
        request = factory.see_orderbook(
            address=xrp_krw_address,
            request_id="test_orderbook_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.orderbook.bids) > 0
        assert len(response.orderbook.asks) > 0

        print(f"\n[OK] Orderbook")
        print(f"   Best Bid: KRW {response.orderbook.bids[0].price:.2f} ({response.orderbook.bids[0].size} XRP)")
        print(f"   Best Ask: KRW {response.orderbook.asks[0].price:.2f} ({response.orderbook.asks[0].size} XRP)")

    async def test_05_candles(self, gateway, factory, xrp_krw_address):
        """1-5. 캔들 데이터 조회"""
        request = factory.see_candles(
            address=xrp_krw_address,
            interval="1m",
            limit=10,
            request_id="test_candles_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.candles) > 0

        # SeeCandlesWorker는 DataFrame으로 반환
        import pandas as pd
        assert isinstance(response.candles, pd.DataFrame)
        latest_candle = response.candles.iloc[0]
        print(f"\n[OK] Candles (Latest)")
        print(f"   Timestamp: {latest_candle['timestamp']}")
        print(f"   Open: KRW {latest_candle['open']:.2f}")
        print(f"   High: KRW {latest_candle['high']:.2f}")
        print(f"   Low: KRW {latest_candle['low']:.2f}")
        print(f"   Close: KRW {latest_candle['close']:.2f}")
        print(f"   Volume: {latest_candle['volume']:.2f}")

    async def test_06_initial_balance(self, gateway, factory):
        """1-6. KRW 초기 잔고 조회"""
        request = factory.see_balance(
            currencies=["KRW"],
            request_id="test_balance_initial"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        krw_balance = response.balances.get("KRW")
        assert krw_balance is not None, "KRW balance not found"

        TestState.initial_krw_balance = krw_balance['balance'].amount

        print(f"\n[OK] Initial KRW Balance")
        print(f"   Total: KRW {krw_balance['balance'].amount:.2f}")
        print(f"   Available: KRW {krw_balance['available']:.2f}")

    async def test_07_initial_holdings(self, gateway, factory):
        """1-7. XRP 초기 보유량 조회"""
        request = factory.see_holdings(
            symbols=[fg.Symbol("XRP/KRW")],
            request_id="test_holdings_initial"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        xrp_holding = response.holdings.get("XRP")
        if xrp_holding:
            total = xrp_holding['balance'].get_asset()
            TestState.initial_xrp_holdings = total
            print(f"\n[OK] Initial XRP Holdings")
            print(f"   Total: {total} XRP")
        else:
            TestState.initial_xrp_holdings = 0.0
            print(f"\n[OK] Initial XRP Holdings: 0 XRP")

    async def test_08_initial_open_orders(self, gateway, factory, xrp_krw_address):
        """1-8. 초기 미체결 주문 확인"""
        request = factory.see_open_orders(
            address=xrp_krw_address,
            request_id="test_open_orders_initial"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n[OK] Initial Open Orders: {len(response.orders)}")
        if response.orders:
            print(f"   WARNING: {len(response.orders)} open orders exist!")
            for order in response.orders:
                print(f"   - {order.order_id}: {order.side} {order.amount} @ {order.price}")


@pytest.mark.asyncio
class TestPhase2MarketBuy:
    """Phase 2: MARKET 매수"""

    async def test_10_market_buy_order(self, gateway, factory, xrp_krw_address):
        """2-1. MARKET 매수 10 XRP"""
        import uuid
        client_order_id = f"buy_market_{uuid.uuid4().hex[:16]}"

        # Upbit Market 매수는 quote_quantity(총액) 사용
        buy_amount_krw = 10.0 * TestState.current_price  # 10 XRP 상당 KRW

        request = factory.create_order(
            address=xrp_krw_address,
            side=fg.OrderSide.BUY,
            order_type=fg.OrderType.MARKET,
            quote_quantity=buy_amount_krw,
            client_order_id=client_order_id,
            request_id="test_market_buy_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        # Upbit Market 주문은 즉시 체결되거나 PENDING 상태일 수 있음
        assert response.status in [fg.OrderStatus.FILLED, fg.OrderStatus.PENDING]

        # 주문 ID만 저장 (체결 내역은 다음 테스트에서 조회)
        TestState.market_buy_order_id = response.order_id
        TestState.market_buy_client_order_id = client_order_id

        print(f"\n[REAL TRADE] MARKET Buy Order Created")
        print(f"   Order ID: {response.order_id}")
        print(f"   Status: {response.status.value}")
        print(f"   Amount: KRW {buy_amount_krw:.2f}")

    async def test_11_verify_buy_trades(self, gateway, factory, xrp_krw_address):
        """2-2. Market 매수 체결 내역 조회"""
        import time
        time.sleep(1)  # 체결 대기

        assert TestState.market_buy_order_id is not None

        # SpotOrder 객체 생성 (see_trades에 필요)
        temp_order = fg.SpotOrder(
            order_id=TestState.market_buy_order_id,
            stock_address=xrp_krw_address,
            side=fg.OrderSide.BUY,
            order_type=fg.OrderType.MARKET,
            price=TestState.current_price,
            amount=1.0,  # 임시값
            timestamp=int(time.time() * 1000),
            client_order_id=TestState.market_buy_client_order_id,
        )

        # 체결 내역 조회
        request = factory.see_trades(
            address=xrp_krw_address,
            order=temp_order,
            request_id="test_trades_buy"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.trades) > 0, "No trades found"

        print(f"\n[OK] Market Buy Trades")
        print(f"   Count: {len(response.trades)}")
        for i, trade in enumerate(response.trades[:3], 1):
            print(f"   {i}. {trade.pair.get_asset()} XRP @ KRW {trade.pair.get_value() / trade.pair.get_asset():.2f}")

    async def test_12_verify_holdings_after_buy(self, gateway, factory):
        """2-3. 매수 후 XRP 보유량 확인"""
        request = factory.see_holdings(
            symbols=[fg.Symbol("XRP/KRW")],
            request_id="test_holdings_after_buy"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        xrp_holding = response.holdings.get("XRP")
        assert xrp_holding is not None, "XRP holding not found after buy"

        total = xrp_holding['balance'].get_asset()
        print(f"\n[OK] XRP Holdings After Buy")
        print(f"   Total: {total} XRP")
        print(f"   Available: {xrp_holding['available']} XRP")

        assert total >= 10.0, f"Expected at least 10 XRP, got {total}"


@pytest.mark.asyncio
class TestPhase3LimitOrdersCreate:
    """Phase 3: LIMIT 주문 생성"""

    async def test_20_create_limit_sell_order(self, gateway, factory, xrp_krw_address):
        """3-1. LIMIT 매도 5 XRP (현재가 +10%)"""
        assert TestState.current_price is not None, "Run Phase 1 test_03_ticker first"

        # Upbit은 호가 단위 준수 필요 (100원 단위)
        sell_price = round(TestState.current_price * 1.10 / 100) * 100

        import uuid
        client_order_id = f"sell_limit_{uuid.uuid4().hex[:16]}"

        request = factory.create_order(
            address=xrp_krw_address,
            side=fg.OrderSide.SELL,
            order_type=fg.OrderType.LIMIT,
            asset_quantity=5.0,
            price=sell_price,
            client_order_id=client_order_id,
            request_id="test_create_sell_limit_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status in [fg.OrderStatus.NEW, fg.OrderStatus.PENDING]

        TestState.limit_sell_order = fg.SpotOrder(
            order_id=response.order_id,
            stock_address=xrp_krw_address,
            side=fg.OrderSide.SELL,
            order_type=fg.OrderType.LIMIT,
            price=sell_price,
            amount=5.0,
            timestamp=response.processed_when,
            client_order_id=client_order_id,
            status=response.status
        )

        print(f"\n[OK] LIMIT Sell Order Created")
        print(f"   Order ID: {response.order_id}")
        print(f"   Price: KRW {sell_price:.2f} (current +10%)")
        print(f"   Quantity: 5 XRP")
        print(f"   Status: {response.status}")

    async def test_21_create_limit_buy_order(self, gateway, factory, xrp_krw_address):
        """3-2. LIMIT 매수 5 XRP (현재가 -10%)"""
        assert TestState.current_price is not None

        # Upbit 호가 단위 (100원)
        buy_price = round(TestState.current_price * 0.90 / 100) * 100

        import uuid
        client_order_id = f"buy_limit_{uuid.uuid4().hex[:16]}"

        request = factory.create_order(
            address=xrp_krw_address,
            side=fg.OrderSide.BUY,
            order_type=fg.OrderType.LIMIT,
            asset_quantity=5.0,
            price=buy_price,
            client_order_id=client_order_id,
            request_id="test_create_buy_limit_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status in [fg.OrderStatus.NEW, fg.OrderStatus.PENDING]

        TestState.limit_buy_order = fg.SpotOrder(
            order_id=response.order_id,
            stock_address=xrp_krw_address,
            side=fg.OrderSide.BUY,
            order_type=fg.OrderType.LIMIT,
            price=buy_price,
            amount=5.0,
            timestamp=response.processed_when,
            client_order_id=client_order_id,
            status=response.status
        )

        print(f"\n[OK] LIMIT Buy Order Created")
        print(f"   Order ID: {response.order_id}")
        print(f"   Price: KRW {buy_price:.2f} (current -10%)")
        print(f"   Quantity: 5 XRP")
        print(f"   Status: {response.status}")

    async def test_22_see_open_orders(self, gateway, factory, xrp_krw_address):
        """3-3. 미체결 주문 2개 확인"""
        request = factory.see_open_orders(
            address=xrp_krw_address,
            request_id="test_open_orders_002"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.orders) >= 2, f"Expected at least 2 orders, got {len(response.orders)}"

        print(f"\n[OK] Open Orders: {len(response.orders)}")
        for order in response.orders:
            print(f"   - {order.order_id}: {order.side} {order.amount} @ {order.price}")

    async def test_23_see_sell_order(self, gateway, factory):
        """3-4. 매도 주문 개별 조회"""
        assert TestState.limit_sell_order is not None

        request = factory.see_order(
            order=TestState.limit_sell_order,
            request_id="test_see_sell_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n[OK] Sell Order Status")
        print(f"   Order ID: {response.order.order_id}")
        print(f"   Status: {response.order.status}")
        print(f"   Price: KRW {response.order.price:.2f}")
        print(f"   Amount: {response.order.amount} XRP")

    async def test_24_see_buy_order(self, gateway, factory):
        """3-5. 매수 주문 개별 조회"""
        assert TestState.limit_buy_order is not None

        request = factory.see_order(
            order=TestState.limit_buy_order,
            request_id="test_see_buy_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n[OK] Buy Order Status")
        print(f"   Order ID: {response.order.order_id}")
        print(f"   Status: {response.order.status}")
        print(f"   Price: KRW {response.order.price:.2f}")
        print(f"   Amount: {response.order.amount} XRP")


@pytest.mark.asyncio
class TestPhase4LimitOrdersModify:
    """Phase 4: LIMIT 주문 수정"""

    async def test_30_modify_sell_order(self, gateway, factory, xrp_krw_address):
        """4-1. 매도 주문 수정 (현재가 +15%)"""
        assert TestState.limit_sell_order is not None
        assert TestState.current_price is not None

        # Upbit 호가 단위
        new_price = round(TestState.current_price * 1.15 / 100) * 100

        import uuid
        new_client_order_id = f"sell_limit_{uuid.uuid4().hex[:16]}_mod"

        request = factory.modify_or_replace_order(
            original_order=TestState.limit_sell_order,
            price=new_price,
            client_order_id=new_client_order_id,
            request_id="test_modify_sell_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        # 새 주문 정보로 업데이트
        old_order_id = TestState.limit_sell_order.order_id

        TestState.limit_sell_order = fg.SpotOrder(
            order_id=response.order_id,
            stock_address=xrp_krw_address,
            side=fg.OrderSide.SELL,
            order_type=fg.OrderType.LIMIT,
            price=new_price,
            amount=5.0,
            timestamp=response.processed_when,
            client_order_id=new_client_order_id,
            status=response.status
        )

        print(f"\n[OK] Sell Order Modified")
        print(f"   Old Order Canceled: {old_order_id}")
        print(f"   New Order Created: {response.order_id}")
        print(f"   New Price: KRW {new_price:.2f} (current +15%)")

    async def test_31_modify_buy_order(self, gateway, factory, xrp_krw_address):
        """4-2. 매수 주문 수정 (현재가 -15%)"""
        assert TestState.limit_buy_order is not None
        assert TestState.current_price is not None

        # Upbit 호가 단위
        new_price = round(TestState.current_price * 0.85 / 100) * 100

        import uuid
        new_client_order_id = f"buy_limit_{uuid.uuid4().hex[:16]}_mod"

        request = factory.modify_or_replace_order(
            original_order=TestState.limit_buy_order,
            price=new_price,
            client_order_id=new_client_order_id,
            request_id="test_modify_buy_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        # 새 주문 정보로 업데이트
        old_order_id = TestState.limit_buy_order.order_id

        TestState.limit_buy_order = fg.SpotOrder(
            order_id=response.order_id,
            stock_address=xrp_krw_address,
            side=fg.OrderSide.BUY,
            order_type=fg.OrderType.LIMIT,
            price=new_price,
            amount=5.0,
            timestamp=response.processed_when,
            client_order_id=new_client_order_id,
            status=response.status
        )

        print(f"\n[OK] Buy Order Modified")
        print(f"   Old Order Canceled: {old_order_id}")
        print(f"   New Order Created: {response.order_id}")
        print(f"   New Price: KRW {new_price:.2f} (current -15%)")

    async def test_32_see_open_orders_after_modify(self, gateway, factory, xrp_krw_address):
        """4-3. 수정 후 미체결 주문 확인"""
        request = factory.see_open_orders(
            address=xrp_krw_address,
            request_id="test_open_orders_after_modify"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.orders) >= 2, f"Expected at least 2 orders, got {len(response.orders)}"

        print(f"\n[OK] Open Orders After Modify: {len(response.orders)}")
        for order in response.orders:
            print(f"   - {order.order_id}: {order.side} {order.amount} @ {order.price}")


@pytest.mark.asyncio
class TestPhase5LimitOrdersCancel:
    """Phase 5: LIMIT 주문 취소"""

    async def test_40_cancel_sell_order(self, gateway, factory):
        """5-1. 매도 주문 취소"""
        assert TestState.limit_sell_order is not None

        request = factory.cancel_order(
            order=TestState.limit_sell_order,
            request_id="test_cancel_sell_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == fg.OrderStatus.CANCELED

        print(f"\n[OK] Sell Order Canceled")
        print(f"   Order ID: {response.order_id}")
        print(f"   Canceled: {response.remaining_amount} XRP")

    async def test_41_cancel_buy_order(self, gateway, factory):
        """5-2. 매수 주문 취소"""
        assert TestState.limit_buy_order is not None

        request = factory.cancel_order(
            order=TestState.limit_buy_order,
            request_id="test_cancel_buy_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert response.status == fg.OrderStatus.CANCELED

        print(f"\n[OK] Buy Order Canceled")
        print(f"   Order ID: {response.order_id}")
        print(f"   Canceled: {response.remaining_amount} XRP")

    async def test_42_see_open_orders_after_cancel(self, gateway, factory, xrp_krw_address):
        """5-3. 취소 후 미체결 주문 확인"""
        request = factory.see_open_orders(
            address=xrp_krw_address,
            request_id="test_open_orders_after_cancel"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n[OK] Open Orders After Cancel: {len(response.orders)}")
        if response.orders:
            for order in response.orders:
                print(f"   - {order.order_id}: {order.side} {order.amount} @ {order.price}")


@pytest.mark.asyncio
class TestPhase6MarketSell:
    """Phase 6: MARKET 매도 (정리)"""

    async def test_50_market_sell_order(self, gateway, factory, xrp_krw_address):
        """6-1. MARKET 매도 10 XRP (전량)"""
        import uuid
        client_order_id = f"sell_market_{uuid.uuid4().hex[:16]}"

        request = factory.create_order(
            address=xrp_krw_address,
            side=fg.OrderSide.SELL,
            order_type=fg.OrderType.MARKET,
            asset_quantity=10.0,
            client_order_id=client_order_id,
            request_id="test_market_sell_001"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        # Upbit Market 주문은 즉시 체결되거나 PENDING 상태일 수 있음
        assert response.status in [fg.OrderStatus.FILLED, fg.OrderStatus.PENDING]

        # 주문 ID만 저장
        TestState.market_sell_order_id = response.order_id
        TestState.market_sell_client_order_id = client_order_id

        print(f"\n[REAL TRADE] MARKET Sell Order Created")
        print(f"   Order ID: {response.order_id}")
        print(f"   Status: {response.status.value}")
        print(f"   Amount: 10.0 XRP")

    async def test_51_verify_sell_trades(self, gateway, factory, xrp_krw_address):
        """6-2. Market 매도 체결 내역 조회"""
        import time
        time.sleep(1)  # 체결 대기

        assert TestState.market_sell_order_id is not None

        # SpotOrder 객체 생성 (see_trades에 필요)
        temp_order = fg.SpotOrder(
            order_id=TestState.market_sell_order_id,
            stock_address=xrp_krw_address,
            side=fg.OrderSide.SELL,
            order_type=fg.OrderType.MARKET,
            price=TestState.current_price,
            amount=10.0,
            timestamp=int(time.time() * 1000),
            client_order_id=TestState.market_sell_client_order_id,
        )

        # 체결 내역 조회
        request = factory.see_trades(
            address=xrp_krw_address,
            order=temp_order,
            request_id="test_trades_sell"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"
        assert len(response.trades) > 0, "No trades found"

        print(f"\n[OK] Market Sell Trades")
        print(f"   Count: {len(response.trades)}")
        for i, trade in enumerate(response.trades[:3], 1):
            print(f"   {i}. {trade.pair.get_asset()} XRP @ KRW {trade.pair.get_value() / trade.pair.get_asset():.2f}")

    async def test_52_verify_holdings_after_sell(self, gateway, factory):
        """6-3. 매도 후 XRP 보유량 확인"""
        request = factory.see_holdings(
            symbols=[fg.Symbol("XRP/KRW")],
            request_id="test_holdings_after_sell"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        xrp_holding = response.holdings.get("XRP")
        if xrp_holding:
            total = xrp_holding['balance'].get_asset()
            print(f"\n[OK] XRP Holdings After Sell: {total} XRP")
        else:
            total = 0.0
            print(f"\n[OK] XRP Holdings After Sell: 0 XRP")

        TestState.final_xrp_holdings = total


@pytest.mark.asyncio
class TestPhase7FinalState:
    """Phase 7: 최종 상태 및 손익 계산"""

    async def test_60_final_open_orders(self, gateway, factory, xrp_krw_address):
        """7-1. 최종 미체결 주문 확인"""
        request = factory.see_open_orders(
            address=xrp_krw_address,
            request_id="test_open_orders_final"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        print(f"\n[OK] Final Open Orders: {len(response.orders)}")
        if response.orders:
            for order in response.orders:
                print(f"   - {order.order_id}: {order.side} {order.amount} @ {order.price}")

    async def test_61_final_holdings(self, gateway, factory):
        """7-2. 최종 XRP 보유량 확인"""
        request = factory.see_holdings(
            symbols=[fg.Symbol("XRP/KRW")],
            request_id="test_holdings_final"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        xrp_holding = response.holdings.get("XRP")
        if xrp_holding:
            total = xrp_holding['balance'].get_asset()
            print(f"\n[FINAL] XRP Holdings: {total} XRP")
        else:
            print(f"\n[FINAL] XRP Holdings: 0 XRP")

    async def test_62_final_balance(self, gateway, factory):
        """7-3. 최종 KRW 잔고 확인"""
        request = factory.see_balance(
            currencies=["KRW"],
            request_id="test_balance_final"
        )

        response = await gateway.execute(request)

        assert response.is_success, f"Failed: {response.error_message}"

        krw_balance = response.balances.get("KRW")
        if krw_balance:
            TestState.final_krw_balance = krw_balance['balance'].amount
            print(f"\n[FINAL] KRW Balance: KRW {krw_balance['balance'].amount:.2f}")
        else:
            print(f"\n[FINAL] KRW Balance: 0")

    async def test_63_trading_summary(self, gateway, factory):
        """7-4. 거래 손익 및 요약 보고"""

        # 1. 손익 계산
        initial_krw = TestState.initial_krw_balance
        final_krw = TestState.final_krw_balance
        trading_cost = initial_krw - final_krw

        # 2. 거래 내역 요약
        buy_trades = TestState.buy_trades
        sell_trades = TestState.sell_trades

        assert buy_trades is not None, "No buy trades found"
        assert sell_trades is not None, "No sell trades found"

        total_buy_xrp = sum(trade.pair.get_asset() for trade in buy_trades)
        total_buy_krw = sum(trade.pair.get_value() for trade in buy_trades)
        avg_buy_price = total_buy_krw / total_buy_xrp if total_buy_xrp > 0 else 0

        total_sell_xrp = sum(trade.pair.get_asset() for trade in sell_trades)
        total_sell_krw = sum(trade.pair.get_value() for trade in sell_trades)
        avg_sell_price = total_sell_krw / total_sell_xrp if total_sell_xrp > 0 else 0

        # 3. 수수료 계산
        total_buy_fees = sum(
            trade.fee.amount if trade.fee else 0
            for trade in buy_trades
        )
        total_sell_fees = sum(
            trade.fee.amount if trade.fee else 0
            for trade in sell_trades
        )
        total_fees = total_buy_fees + total_sell_fees

        # 4. 가격 영향
        price_impact = total_sell_krw - total_buy_krw

        print(f"\n{'='*60}")
        print(f"[TRADING SUMMARY]")
        print(f"{'='*60}")
        print(f"\n[Initial State]")
        print(f"   KRW Balance: KRW {initial_krw:.2f}")
        print(f"   XRP Holdings: {TestState.initial_xrp_holdings} XRP")

        print(f"\n[Buy Transactions]")
        print(f"   Total XRP Bought: {total_buy_xrp} XRP")
        print(f"   Total KRW Spent: KRW {total_buy_krw:.2f}")
        print(f"   Average Buy Price: KRW {avg_buy_price:.2f}")
        print(f"   Trades: {len(buy_trades)}")
        print(f"   Fees: KRW {total_buy_fees:.2f}")

        print(f"\n[Sell Transactions]")
        print(f"   Total XRP Sold: {total_sell_xrp} XRP")
        print(f"   Total KRW Received: KRW {total_sell_krw:.2f}")
        print(f"   Average Sell Price: KRW {avg_sell_price:.2f}")
        print(f"   Trades: {len(sell_trades)}")
        print(f"   Fees: KRW {total_sell_fees:.2f}")

        print(f"\n[Final State]")
        print(f"   KRW Balance: KRW {final_krw:.2f}")
        print(f"   XRP Holdings: {TestState.final_xrp_holdings} XRP")
        print(f"   Open Orders: 0")

        print(f"\n[Cost Analysis]")
        print(f"   Trading Cost: KRW {trading_cost:.2f}")
        print(f"   Total Fees: KRW {total_fees:.2f}")
        print(f"   Price Impact: KRW {price_impact:.2f}")
        print(f"   Net P&L: KRW {-trading_cost:.2f}")
        print(f"   P&L %: {(-trading_cost / initial_krw * 100):.4f}%")
        print(f"{'='*60}\n")

        # Assertion: 거래 비용이 합리적인지 확인
        assert trading_cost > 0, "Trading should have cost (fees + slippage)"
        assert trading_cost < total_buy_krw * 0.02, f"Trading cost too high (>{total_buy_krw * 0.02:.2f})"
