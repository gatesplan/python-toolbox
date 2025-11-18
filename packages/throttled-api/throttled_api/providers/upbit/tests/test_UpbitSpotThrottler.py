"""
UpbitSpotThrottler tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from throttled_api.providers.upbit.UpbitSpotThrottler import UpbitSpotThrottler


@pytest.fixture
def mock_client():
    """Mock Upbit client"""
    client = MagicMock()

    # Quotation API mocks
    client.get_market_all = AsyncMock(return_value=[{"market": "KRW-BTC"}])
    client.get_ticker = AsyncMock(return_value=[{"market": "KRW-BTC", "trade_price": 50000000}])
    client.get_candles_minutes = AsyncMock(return_value=[{"market": "KRW-BTC"}])
    client.get_candles_days = AsyncMock(return_value=[{"market": "KRW-BTC"}])
    client.get_candles_weeks = AsyncMock(return_value=[{"market": "KRW-BTC"}])
    client.get_candles_months = AsyncMock(return_value=[{"market": "KRW-BTC"}])
    client.get_orderbook = AsyncMock(return_value=[{"market": "KRW-BTC"}])
    client.get_trades_ticks = AsyncMock(return_value=[{"market": "KRW-BTC"}])

    # Account API mocks
    client.get_accounts = AsyncMock(return_value=[{"currency": "KRW", "balance": "1000000"}])
    client.get_api_keys = AsyncMock(return_value=[{"access_key": "test"}])

    # Trading API mocks
    client.create_order = AsyncMock(return_value={"uuid": "order-123"})
    client.cancel_order = AsyncMock(return_value={"uuid": "order-123"})
    client.get_order = AsyncMock(return_value={"uuid": "order-123"})
    client.get_orders = AsyncMock(return_value=[{"uuid": "order-123"}])
    client.get_orders_chance = AsyncMock(return_value={"market": "KRW-BTC"})
    client.get_orders_open = AsyncMock(return_value=[])
    client.get_orders_closed = AsyncMock(return_value=[])

    # Deposits API mocks
    client.get_deposits = AsyncMock(return_value=[])
    client.get_deposit = AsyncMock(return_value={"uuid": "deposit-123"})
    client.generate_coin_address = AsyncMock(return_value={"currency": "BTC"})
    client.get_coin_addresses = AsyncMock(return_value=[])
    client.get_coin_address = AsyncMock(return_value={"currency": "BTC"})
    client.create_krw_deposit = AsyncMock(return_value={"amount": "10000"})

    # Withdrawals API mocks
    client.get_withdraws = AsyncMock(return_value=[])
    client.get_withdraw = AsyncMock(return_value={"uuid": "withdraw-123"})
    client.get_withdraws_chance = AsyncMock(return_value={"currency": "BTC"})
    client.withdraw_coin = AsyncMock(return_value={"uuid": "withdraw-123"})
    client.withdraw_krw = AsyncMock(return_value={"amount": "10000"})

    return client


class TestUpbitSpotThrottlerInit:
    """UpbitSpotThrottler 초기화 테스트"""

    def test_initialization(self, mock_client):
        """기본 초기화"""
        throttler = UpbitSpotThrottler(client=mock_client)

        assert throttler.client == mock_client
        assert throttler.warning_threshold == 0.2
        assert len(throttler.pipelines) == 6

        # Pipeline 이름 확인
        timeframes = [p.timeframe for p in throttler.pipelines]
        assert "QUOTATION_1S" in timeframes
        assert "QUOTATION_1M" in timeframes
        assert "EXCHANGE_ORDER_1S" in timeframes
        assert "EXCHANGE_ORDER_1M" in timeframes
        assert "EXCHANGE_NON_ORDER_1S" in timeframes
        assert "EXCHANGE_NON_ORDER_1M" in timeframes


class TestQuotationEndpoints:
    """Quotation API 테스트"""

    @pytest.mark.anyio
    async def test_get_market_all(self, mock_client):
        """마켓 코드 조회"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.get_market_all()

        assert result == [{"market": "KRW-BTC"}]
        mock_client.get_market_all.assert_called_once()

    @pytest.mark.anyio
    async def test_get_ticker(self, mock_client):
        """현재가 조회"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.get_ticker(markets=["KRW-BTC"])

        assert result[0]["market"] == "KRW-BTC"
        mock_client.get_ticker.assert_called_once()

    @pytest.mark.anyio
    async def test_get_candles_minutes(self, mock_client):
        """분봉 캔들 조회"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.get_candles_minutes(
            unit=1, market="KRW-BTC", count=10
        )

        assert result[0]["market"] == "KRW-BTC"
        mock_client.get_candles_minutes.assert_called_once()


class TestTradingEndpoints:
    """Trading API 테스트"""

    @pytest.mark.anyio
    async def test_create_order(self, mock_client):
        """주문 생성"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.create_order(
            market="KRW-BTC",
            side="bid",
            ord_type="limit",
            volume="0.01",
            price="50000000",
        )

        assert result["uuid"] == "order-123"
        mock_client.create_order.assert_called_once()

    @pytest.mark.anyio
    async def test_cancel_order(self, mock_client):
        """주문 취소"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.cancel_order(uuid="order-123")

        assert result["uuid"] == "order-123"
        mock_client.cancel_order.assert_called_once()

    @pytest.mark.anyio
    async def test_get_order(self, mock_client):
        """주문 조회"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.get_order(uuid="order-123")

        assert result["uuid"] == "order-123"
        mock_client.get_order.assert_called_once()


class TestAccountEndpoints:
    """Account API 테스트"""

    @pytest.mark.anyio
    async def test_get_accounts(self, mock_client):
        """계좌 조회"""
        throttler = UpbitSpotThrottler(client=mock_client)
        result = await throttler.get_accounts()

        assert result[0]["currency"] == "KRW"
        mock_client.get_accounts.assert_called_once()


class TestRateLimiting:
    """Rate Limiting 동작 테스트"""

    @pytest.mark.anyio
    async def test_quotation_rate_limit(self, mock_client):
        """QUOTATION 카테고리 rate limiting"""
        throttler = UpbitSpotThrottler(client=mock_client)

        # 10회 연속 호출 (QUOTATION_1S limit=10)
        for _ in range(10):
            await throttler.get_ticker(markets=["KRW-BTC"])

        # 모든 호출 성공 확인
        assert mock_client.get_ticker.call_count == 10

    @pytest.mark.anyio
    async def test_mixed_category_rate_limit(self, mock_client):
        """서로 다른 카테고리는 독립적으로 제한"""
        throttler = UpbitSpotThrottler(client=mock_client)

        # QUOTATION 5회
        for _ in range(5):
            await throttler.get_ticker(markets=["KRW-BTC"])

        # EXCHANGE_NON_ORDER 5회 (독립적)
        for _ in range(5):
            await throttler.get_accounts()

        assert mock_client.get_ticker.call_count == 5
        assert mock_client.get_accounts.call_count == 5

    @pytest.mark.anyio
    async def test_order_rate_limit(self, mock_client):
        """EXCHANGE_ORDER 카테고리 rate limiting"""
        throttler = UpbitSpotThrottler(client=mock_client)

        # 8회 연속 주문 (EXCHANGE_ORDER_1S limit=8)
        for _ in range(8):
            await throttler.create_order(
                market="KRW-BTC",
                side="bid",
                ord_type="limit",
                volume="0.01",
                price="50000000",
            )

        assert mock_client.create_order.call_count == 8
