"""
BinanceSpotThrottler tests
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from throttled_api.providers.binance.BinanceSpotThrottler import BinanceSpotThrottler
from throttled_api.providers.binance.exceptions import UnknownEndpointError


pytestmark = pytest.mark.anyio


class MockBinanceClient:
    """Binance 클라이언트 mock"""

    def __init__(self):
        self.request_called = []
        self.method_calls = []  # (method_name, args, kwargs)

    async def request(self, method, endpoint, params=None, **kwargs):
        """요청 기록"""
        self.request_called.append((method, endpoint, params))
        # Mock 응답
        mock_response = Mock()
        mock_response.headers = {
            "X-MBX-USED-WEIGHT-1M": "10",
        }
        return mock_response

    # GeneralMixin methods
    async def ping(self):
        self.method_calls.append(("ping", (), {}))
        return {"status": "ok"}

    async def get_server_time(self):
        self.method_calls.append(("get_server_time", (), {}))
        return {"serverTime": 1234567890000}

    async def get_exchange_info(self, symbol=None, symbols=None):
        self.method_calls.append(("get_exchange_info", (), {"symbol": symbol, "symbols": symbols}))
        return {"symbols": []}

    # MarketDataMixin methods
    async def get_order_book(self, symbol, limit=100):
        self.method_calls.append(("get_order_book", (), {"symbol": symbol, "limit": limit}))
        return {"lastUpdateId": 12345, "bids": [], "asks": []}

    async def get_ticker_price(self, symbol=None, symbols=None):
        self.method_calls.append(("get_ticker_price", (), {"symbol": symbol, "symbols": symbols}))
        return {"symbol": symbol, "price": "50000.00"}

    # TradingMixin methods
    async def create_order(self, symbol, side, type, **kwargs):
        self.method_calls.append(("create_order", (), {"symbol": symbol, "side": side, "type": type, **kwargs}))
        return {"orderId": 12345, "status": "NEW"}

    # AccountMixin methods
    async def get_account(self):
        self.method_calls.append(("get_account", (), {}))
        return {"balances": []}

    async def get_open_orders(self, symbol=None):
        self.method_calls.append(("get_open_orders", (), {"symbol": symbol}))
        return []

    # UserDataStreamMixin methods
    async def create_listen_key(self):
        self.method_calls.append(("create_listen_key", (), {}))
        return {"listenKey": "test_listen_key"}


class TestBinanceSpotThrottlerInitialization:
    """초기화 테스트"""

    def test_init_with_client(self):
        """클라이언트로 초기화"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        assert throttler.client is client
        assert len(throttler.pipelines) == 1  # REQUEST_WEIGHT만

    def test_init_with_raw_requests_limit(self):
        """RAW_REQUESTS 제한 활성화"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client, enable_raw_requests_limit=True)

        assert len(throttler.pipelines) == 2  # REQUEST_WEIGHT + RAW_REQUESTS


class TestBinanceSpotThrottlerMixinMethods:
    """Mixin 메서드 테스트"""

    async def test_ping(self):
        """ping 메서드"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.ping()

        assert result == {"status": "ok"}
        assert len(client.method_calls) == 1
        assert client.method_calls[0][0] == "ping"
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 1

    async def test_get_server_time(self):
        """get_server_time 메서드"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_server_time()

        assert result == {"serverTime": 1234567890000}
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 1

    async def test_get_exchange_info_no_symbol(self):
        """get_exchange_info symbol 없음 (weight=20)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_exchange_info()

        assert result == {"symbols": []}
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 20

    async def test_get_exchange_info_with_symbol(self):
        """get_exchange_info symbol 있음 (weight=2)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_exchange_info(symbol="BTCUSDT")

        assert result == {"symbols": []}
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 2

    async def test_get_order_book_limit_100(self):
        """get_order_book limit=100 (weight=5)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_order_book(symbol="BTCUSDT", limit=100)

        assert result["lastUpdateId"] == 12345
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 5

    async def test_get_order_book_limit_500(self):
        """get_order_book limit=500 (weight=25)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_order_book(symbol="BTCUSDT", limit=500)

        assert throttler.weight_pipeline.window.remaining == initial_remaining - 25

    async def test_get_ticker_price_single_symbol(self):
        """get_ticker_price 단일 symbol (weight=2)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_ticker_price(symbol="BTCUSDT")

        assert result["symbol"] == "BTCUSDT"
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 2

    async def test_get_ticker_price_all_symbols(self):
        """get_ticker_price 전체 symbol (weight=4)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_ticker_price()

        assert throttler.weight_pipeline.window.remaining == initial_remaining - 4

    async def test_create_order(self):
        """create_order (weight=1)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="LIMIT",
            quantity=0.1,
            price=50000,
        )

        assert result["orderId"] == 12345
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 1

    async def test_get_account(self):
        """get_account (weight=20)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_account()

        assert result == {"balances": []}
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 20

    async def test_get_open_orders_with_symbol(self):
        """get_open_orders symbol 있음 (weight=6)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_open_orders(symbol="BTCUSDT")

        assert result == []
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 6

    async def test_get_open_orders_all_symbols(self):
        """get_open_orders 전체 symbol (weight=80)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.get_open_orders()

        assert result == []
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 80

    async def test_create_listen_key(self):
        """create_listen_key (weight=2)"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining
        result = await throttler.create_listen_key()

        assert result["listenKey"] == "test_listen_key"
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 2


class TestBinanceSpotThrottlerConcurrency:
    """동시성 테스트"""

    async def test_concurrent_requests(self):
        """동시 요청이 순차적으로 처리"""
        client = MockBinanceClient()
        throttler = BinanceSpotThrottler(client=client)

        initial_remaining = throttler.weight_pipeline.window.remaining

        # 10개 요청 동시 실행 (각 weight=1)
        tasks = [throttler.ping() for _ in range(10)]
        await asyncio.gather(*tasks)

        assert len(client.method_calls) == 10
        assert throttler.weight_pipeline.window.remaining == initial_remaining - 10
