# BinanceSpotGateway 테스트

import os
import pytest
from unittest.mock import Mock, patch
from financial_gateway.spot.binance_spot_gateway import BinanceSpotGateway


class TestBinanceSpotGatewayInit:
    # 초기화 테스트

    def test_init_with_valid_api_keys(self):
        # API Key가 있으면 정상 초기화
        os.environ["BINANCE_SPOT_API_KEY"] = "test_key"
        os.environ["BINANCE_SPOT_API_SECRET"] = "test_secret"

        try:
            gateway = BinanceSpotGateway()

            assert gateway.gateway_name == "binance"
            assert gateway.is_realworld_gateway is True
            assert gateway._api_key == "test_key"
            assert gateway._api_secret == "test_secret"
        finally:
            del os.environ["BINANCE_SPOT_API_KEY"]
            del os.environ["BINANCE_SPOT_API_SECRET"]

    def test_init_missing_api_key_raises_error(self):
        # API Key가 없으면 EnvironmentError 발생
        os.environ["BINANCE_SPOT_API_SECRET"] = "test_secret"

        try:
            with pytest.raises(EnvironmentError, match="BINANCE_SPOT_API_KEY"):
                BinanceSpotGateway()
        finally:
            if "BINANCE_SPOT_API_SECRET" in os.environ:
                del os.environ["BINANCE_SPOT_API_SECRET"]

    def test_init_missing_api_secret_raises_error(self):
        # API Secret이 없으면 EnvironmentError 발생
        os.environ["BINANCE_SPOT_API_KEY"] = "test_key"

        try:
            with pytest.raises(EnvironmentError, match="BINANCE_SPOT_API_SECRET"):
                BinanceSpotGateway()
        finally:
            if "BINANCE_SPOT_API_KEY" in os.environ:
                del os.environ["BINANCE_SPOT_API_KEY"]

    def test_init_creates_binance_client(self):
        # Binance Spot 클라이언트가 생성되는지 확인
        os.environ["BINANCE_SPOT_API_KEY"] = "test_key"
        os.environ["BINANCE_SPOT_API_SECRET"] = "test_secret"

        try:
            with patch("financial_gateway.spot.binance_spot_gateway.Spot") as mock_spot:
                gateway = BinanceSpotGateway()

                mock_spot.assert_called_once_with(
                    api_key="test_key",
                    api_secret="test_secret"
                )
                assert gateway._client == mock_spot.return_value
        finally:
            del os.environ["BINANCE_SPOT_API_KEY"]
            del os.environ["BINANCE_SPOT_API_SECRET"]


class TestBinanceSpotGatewayLimitBuyOrder:
    # 지정가 매수 주문 테스트

    @pytest.fixture
    def gateway(self):
        # 테스트용 게이트웨이 fixture
        os.environ["BINANCE_SPOT_API_KEY"] = "test_key"
        os.environ["BINANCE_SPOT_API_SECRET"] = "test_secret"

        try:
            with patch("financial_gateway.spot.binance_spot_gateway.Spot"):
                gateway = BinanceSpotGateway()
                gateway._client = Mock()
                yield gateway
        finally:
            del os.environ["BINANCE_SPOT_API_KEY"]
            del os.environ["BINANCE_SPOT_API_SECRET"]

    def test_request_limit_buy_order_success(self, gateway):
        # 지정가 매수 주문 성공 케이스
        from financial_assets.request import LimitBuyOrderRequest
        from financial_assets.stock_address import StockAddress

        # Mock API 응답
        gateway._client.new_order.return_value = {
            "orderId": 12345,
            "symbol": "BTCUSDT",
            "status": "NEW",
            "price": "50000.00",
            "origQty": "0.1",
            "executedQty": "0.0"
        }

        # 요청 생성
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        request = LimitBuyOrderRequest(
            address=address,
            price=50000.0,
            volume=0.1
        )

        # 실행
        response = gateway.request_limit_buy_order(request)

        # 검증
        assert response.is_success is True
        assert response.order is not None
        gateway._client.new_order.assert_called_once()


class TestBinanceSpotGatewayMarketBuyOrder:
    # 시장가 매수 주문 테스트

    @pytest.fixture
    def gateway(self):
        # 테스트용 게이트웨이 fixture
        os.environ["BINANCE_SPOT_API_KEY"] = "test_key"
        os.environ["BINANCE_SPOT_API_SECRET"] = "test_secret"

        try:
            with patch("financial_gateway.spot.binance_spot_gateway.Spot"):
                gateway = BinanceSpotGateway()
                gateway._client = Mock()
                yield gateway
        finally:
            del os.environ["BINANCE_SPOT_API_KEY"]
            del os.environ["BINANCE_SPOT_API_SECRET"]

    def test_request_market_buy_order_success(self, gateway):
        # 시장가 매수 주문 성공 케이스
        from financial_assets.request import MarketBuyOrderRequest
        from financial_assets.stock_address import StockAddress

        # Mock API 응답
        gateway._client.new_order.return_value = {
            "orderId": 12346,
            "symbol": "BTCUSDT",
            "status": "FILLED",
            "origQty": "0.1",
            "executedQty": "0.1"
        }

        # 요청 생성
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m"
        )
        request = MarketBuyOrderRequest(
            address=address,
            volume=0.1
        )

        # 실행
        response = gateway.request_market_buy_order(request)

        # 검증
        assert response.is_success is True
        assert response.order is not None
        gateway._client.new_order.assert_called_once()
