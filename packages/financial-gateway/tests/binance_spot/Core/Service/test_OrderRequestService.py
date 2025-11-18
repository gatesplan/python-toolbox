"""
Service/OrderRequestService 테스트
Core 계층을 조합하여 주문 관련 비즈니스 로직 제공
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from financial_gateway.binance_spot.Core.Service.OrderRequestService import OrderRequestService
from financial_gateway.request import (
    LimitBuyOrderRequest,
    LimitSellOrderRequest,
    MarketBuyOrderRequest,
    MarketSellOrderRequest,
    CloseOrderRequest,
    OrderCurrentStateRequest,
)
from financial_assets.stock_address import StockAddress
from financial_assets.constants import Side, OrderType, OrderStatus


@pytest.fixture
def btc_usdt_address():
    """BTC/USDT 주소"""
    return StockAddress(
        archetype="candle",
        exchange="binance",
        tradetype="spot",
        base="BTC",
        quote="USDT",
        timeframe="1m",
    )


class TestOrderRequestService:
    """OrderRequestService 테스트"""

    @pytest.mark.asyncio
    async def test_limit_buy_success(self, btc_usdt_address):
        """지정가 매수 주문 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            # Mock APICallExecutor
            mock_executor = MagicMock()
            mock_executor.create_order = AsyncMock(return_value={
                "symbol": "BTCUSDT",
                "orderId": 12345,
                "side": "BUY",
                "type": "LIMIT",
                "price": "50000.00",
                "origQty": "0.001",
                "executedQty": "0",
                "status": "NEW",
                "timeInForce": "GTC",
                "transactTime": 1234567890,
            })
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = LimitBuyOrderRequest(
                address=btc_usdt_address,
                price=50000.0,
                volume=0.001,
                post_only=False,
            )

            response = await service.limit_buy(request)

            assert response.is_success is True
            assert response.order is not None
            assert response.order.order_id == "12345"
            assert response.order.side == Side.BUY
            assert response.order.order_type == OrderType.LIMIT
            assert response.order.price == 50000.0
            assert response.order.amount == 0.001

    @pytest.mark.asyncio
    async def test_limit_sell_with_post_only(self, btc_usdt_address):
        """지정가 매도 주문 (post_only=True)"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.create_order = AsyncMock(return_value={
                "symbol": "BTCUSDT",
                "orderId": 12346,
                "side": "SELL",
                "type": "LIMIT",
                "price": "51000.00",
                "origQty": "0.001",
                "executedQty": "0",
                "status": "NEW",
                "timeInForce": "GTX",
                "transactTime": 1234567890,
            })
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = LimitSellOrderRequest(
                address=btc_usdt_address,
                price=51000.0,
                volume=0.001,
                post_only=True,
            )

            response = await service.limit_sell(request)

            assert response.is_success is True
            assert response.order.side == Side.SELL
            # post_only는 RequestConverter에서 처리됨

    @pytest.mark.asyncio
    async def test_market_buy_success(self, btc_usdt_address):
        """시장가 매수 주문 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.create_order = AsyncMock(return_value={
                "symbol": "BTCUSDT",
                "orderId": 12347,
                "side": "BUY",
                "type": "MARKET",
                "origQty": "0.001",
                "executedQty": "0.001",
                "status": "FILLED",
                "transactTime": 1234567890,
            })
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = MarketBuyOrderRequest(
                address=btc_usdt_address,
                volume=0.001,
            )

            response = await service.market_buy(request)

            assert response.is_success is True
            assert response.order.order_type == OrderType.MARKET
            assert response.order.status == OrderStatus.FILLED

    @pytest.mark.asyncio
    async def test_market_sell_success(self, btc_usdt_address):
        """시장가 매도 주문 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.create_order = AsyncMock(return_value={
                "symbol": "BTCUSDT",
                "orderId": 12348,
                "side": "SELL",
                "type": "MARKET",
                "origQty": "0.001",
                "executedQty": "0.001",
                "status": "FILLED",
                "transactTime": 1234567890,
            })
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = MarketSellOrderRequest(
                address=btc_usdt_address,
                volume=0.001,
            )

            response = await service.market_sell(request)

            assert response.is_success is True
            assert response.order.side == Side.SELL

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, btc_usdt_address):
        """주문 취소 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.cancel_order = AsyncMock(return_value={
                "symbol": "BTCUSDT",
                "orderId": 12345,
                "status": "CANCELED",
            })
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = CloseOrderRequest(
                address=btc_usdt_address,
                order_id="12345",
            )

            response = await service.cancel_order(request)

            assert response.is_success is True

    @pytest.mark.asyncio
    async def test_get_order_status_success(self, btc_usdt_address):
        """주문 상태 조회 성공"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.get_order = AsyncMock(return_value={
                "symbol": "BTCUSDT",
                "orderId": 12345,
                "side": "BUY",
                "type": "LIMIT",
                "price": "50000.00",
                "origQty": "0.001",
                "executedQty": "0.0005",
                "status": "PARTIALLY_FILLED",
                "timeInForce": "GTC",
                "time": 1234567890,
            })
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = OrderCurrentStateRequest(
                address=btc_usdt_address,
                order_id="12345",
            )

            response = await service.get_order_status(request)

            assert response.is_success is True
            assert response.current_order is not None
            assert response.current_order.status == OrderStatus.PARTIAL
            assert response.current_order.filled_amount == 0.0005

    @pytest.mark.asyncio
    async def test_order_error_handling(self, btc_usdt_address):
        """주문 실패 시 에러 처리"""
        with patch("financial_gateway.binance_spot.Core.Service.OrderRequestService.APICallExecutor") as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor.create_order = AsyncMock(side_effect=Exception("Insufficient balance"))
            mock_executor_class.return_value = mock_executor

            service = OrderRequestService()
            request = LimitBuyOrderRequest(
                address=btc_usdt_address,
                price=50000.0,
                volume=10.0,  # 잔고 부족
                post_only=False,
            )

            response = await service.limit_buy(request)

            assert response.is_success is False
            assert response.error_message is not None
            assert "insufficient" in response.error_message.lower()
            assert response.is_insufficient_balance is True
