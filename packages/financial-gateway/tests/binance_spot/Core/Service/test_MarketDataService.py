"""
Service/MarketDataService 테스트
Core 계층을 조합하여 시장 데이터 조회 기능 제공
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from financial_gateway.binance_spot.Core.Service.MarketDataService import MarketDataService
from financial_gateway.request import (
    TickerRequest,
    OrderbookRequest,
    CurrentBalanceRequest,
)
from financial_assets.stock_address import StockAddress


@pytest.fixture
def xrp_usdt_address():
    """XRP/USDT 주소"""
    return StockAddress(
        archetype="candle",
        exchange="binance",
        tradetype="spot",
        base="XRP",
        quote="USDT",
        timeframe="1m",
    )


class TestMarketDataService:
    """MarketDataService 테스트"""

    @pytest.mark.asyncio
    async def test_get_ticker_success(self, xrp_usdt_address):
        """Ticker 정보 조회 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.MarketDataService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.get_ticker_24hr = AsyncMock(return_value={
                "symbol": "XRPUSDT",
                "openPrice": "2.5000",
                "highPrice": "2.6000",
                "lowPrice": "2.4000",
                "lastPrice": "2.5500",
                "volume": "1000000.00",
                "closeTime": 1234567890,
            })
            mock_executor_class.return_value = mock_executor

            service = MarketDataService()
            request = TickerRequest(address=xrp_usdt_address)

            response = await service.get_ticker(request)

            assert response.is_success is True
            assert "XRPUSDT" in response.result
            assert response.result["XRPUSDT"]["current"] == 2.55
            assert response.result["XRPUSDT"]["open"] == 2.5
            assert response.result["XRPUSDT"]["high"] == 2.6
            assert response.result["XRPUSDT"]["low"] == 2.4

    @pytest.mark.asyncio
    async def test_get_orderbook_success(self, xrp_usdt_address):
        """호가 정보 조회 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.MarketDataService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.get_depth = AsyncMock(return_value={
                "bids": [
                    ["2.5000", "100.00"],
                    ["2.4900", "200.00"],
                ],
                "asks": [
                    ["2.5100", "150.00"],
                    ["2.5200", "250.00"],
                ],
            })
            mock_executor_class.return_value = mock_executor

            service = MarketDataService()
            request = OrderbookRequest(address=xrp_usdt_address, limit=5)

            response = await service.get_orderbook(request)

            assert response.is_success is True
            assert len(response.bids) == 2
            assert len(response.asks) == 2
            assert response.bids[0] == (2.5, 100.0)
            assert response.asks[0] == (2.51, 150.0)

    @pytest.mark.asyncio
    async def test_get_balance_success(self):
        """잔고 조회 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.MarketDataService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.get_account = AsyncMock(return_value={
                "balances": [
                    {"asset": "XRP", "free": "40.00000000", "locked": "6.00000000"},
                    {"asset": "USDT", "free": "1000.00000000", "locked": "0.00000000"},
                    {"asset": "BTC", "free": "0.00000000", "locked": "0.00000000"},
                ]
            })
            mock_executor_class.return_value = mock_executor

            service = MarketDataService()
            request = CurrentBalanceRequest()

            response = await service.get_balance(request)

            assert response.is_success is True
            assert "XRP" in response.result
            assert "USDT" in response.result
            assert "BTC" not in response.result  # 잔고 0은 제외
            assert response.result["XRP"].amount == 46.0  # free + locked
            assert response.result["USDT"].amount == 1000.0

    @pytest.mark.asyncio
    async def test_ticker_error_handling(self, xrp_usdt_address):
        """Ticker 조회 실패 시 에러 처리"""
        with patch("financial_gateway.binance_spot.Core.Service.MarketDataService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.get_ticker_24hr = AsyncMock(side_effect=Exception("Network error"))
            mock_executor_class.return_value = mock_executor

            service = MarketDataService()
            request = TickerRequest(address=xrp_usdt_address)

            response = await service.get_ticker(request)

            assert response.is_success is False
            assert response.error_message is not None
            assert "network" in response.error_message.lower()
