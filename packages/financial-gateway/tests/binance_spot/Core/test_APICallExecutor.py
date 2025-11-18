import pytest
from unittest.mock import Mock, patch, AsyncMock
from financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor import APICallExecutor


class TestAPICallExecutor:
    """APICallExecutor 테스트"""

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_env_vars_raises_error(self):
        # 환경변수 없이 초기화 시 EnvironmentError 발생
        with pytest.raises(EnvironmentError, match="BINANCE_SPOT_API_KEY"):
            APICallExecutor()

    @patch.dict("os.environ", {"BINANCE_SPOT_API_KEY": "test_key"}, clear=True)
    def test_init_without_secret_raises_error(self):
        # API_SECRET 없이 초기화 시 EnvironmentError 발생
        with pytest.raises(EnvironmentError, match="BINANCE_SPOT_API_SECRET"):
            APICallExecutor()

    @patch.dict(
        "os.environ",
        {"BINANCE_SPOT_API_KEY": "test_key", "BINANCE_SPOT_API_SECRET": "test_secret"},
        clear=True,
    )
    @patch("financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor.BinanceSpotThrottler")
    def test_init_with_valid_env_creates_throttler(self, mock_throttler_class):
        # 유효한 환경변수로 초기화 시 BinanceSpotThrottler 생성
        mock_throttler_instance = Mock()
        mock_throttler_class.return_value = mock_throttler_instance

        executor = APICallExecutor()

        assert executor.throttler is not None
        mock_throttler_class.assert_called_once()

    @patch.dict(
        "os.environ",
        {"BINANCE_SPOT_API_KEY": "test_key", "BINANCE_SPOT_API_SECRET": "test_secret"},
        clear=True,
    )
    @patch("financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor.BinanceSpotThrottler")
    @pytest.mark.asyncio
    async def test_create_order_calls_throttler(self, mock_throttler_class):
        # create_order 호출 시 throttler.create_order 호출
        mock_throttler = Mock()
        mock_throttler.create_order = AsyncMock(return_value={"orderId": 12345})
        mock_throttler_class.return_value = mock_throttler

        executor = APICallExecutor()
        result = await executor.create_order(
            symbol="BTCUSDT", side="BUY", type="LIMIT", quantity=0.001, price=50000.0
        )

        mock_throttler.create_order.assert_called_once_with(
            symbol="BTCUSDT", side="BUY", type="LIMIT", quantity=0.001, price=50000.0
        )
        assert result == {"orderId": 12345}

    @patch.dict(
        "os.environ",
        {"BINANCE_SPOT_API_KEY": "test_key", "BINANCE_SPOT_API_SECRET": "test_secret"},
        clear=True,
    )
    @patch("financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor.BinanceSpotThrottler")
    @pytest.mark.asyncio
    async def test_get_order_book_calls_throttler(self, mock_throttler_class):
        # get_order_book 호출 시 throttler.get_order_book 호출
        mock_throttler = Mock()
        mock_throttler.get_order_book = AsyncMock(
            return_value={"bids": [[50000, 1.0]], "asks": [[50100, 1.0]]}
        )
        mock_throttler_class.return_value = mock_throttler

        executor = APICallExecutor()
        result = await executor.get_order_book(symbol="BTCUSDT", limit=100)

        mock_throttler.get_order_book.assert_called_once_with(symbol="BTCUSDT", limit=100)
        assert result == {"bids": [[50000, 1.0]], "asks": [[50100, 1.0]]}

    @patch.dict(
        "os.environ",
        {"BINANCE_SPOT_API_KEY": "test_key", "BINANCE_SPOT_API_SECRET": "test_secret"},
        clear=True,
    )
    @patch("financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor.BinanceSpotThrottler")
    @pytest.mark.asyncio
    async def test_cancel_order_calls_throttler(self, mock_throttler_class):
        # cancel_order 호출 시 throttler.cancel_order 호출
        mock_throttler = Mock()
        mock_throttler.cancel_order = AsyncMock(return_value={"orderId": 12345, "status": "CANCELED"})
        mock_throttler_class.return_value = mock_throttler

        executor = APICallExecutor()
        result = await executor.cancel_order(symbol="BTCUSDT", order_id=12345)

        mock_throttler.cancel_order.assert_called_once_with(symbol="BTCUSDT", order_id=12345)
        assert result == {"orderId": 12345, "status": "CANCELED"}

    @patch.dict(
        "os.environ",
        {"BINANCE_SPOT_API_KEY": "test_key", "BINANCE_SPOT_API_SECRET": "test_secret"},
        clear=True,
    )
    @patch("financial_gateway.binance_spot.Core.APICallExecutor.APICallExecutor.BinanceSpotThrottler")
    @pytest.mark.asyncio
    async def test_get_account_info_calls_throttler(self, mock_throttler_class):
        # get_account_info 호출 시 throttler.get_account_info 호출
        mock_throttler = Mock()
        mock_throttler.get_account_info = AsyncMock(return_value={"balances": []})
        mock_throttler_class.return_value = mock_throttler

        executor = APICallExecutor()
        result = await executor.get_account_info()

        mock_throttler.get_account_info.assert_called_once()
        assert result == {"balances": []}
