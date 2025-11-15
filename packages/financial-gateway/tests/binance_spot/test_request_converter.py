"""RequestConverter 테스트 - Request 객체를 Binance API 파라미터로 변환"""

import pytest
from financial_assets.stock_address import StockAddress
from financial_gateway.request import (
    LimitBuyOrderRequest,
    LimitSellOrderRequest,
    MarketBuyOrderRequest,
    MarketSellOrderRequest,
)
from financial_gateway.binance_spot.Core.RequestConverter.RequestConverter import (
    RequestConverter,
)


class TestRequestConverterLimitOrders:
    """지정가 주문 변환 테스트"""

    def test_convert_limit_buy_order_basic(self):
        """기본 지정가 매수 주문 변환"""
        # Arrange
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m",
        )
        request = LimitBuyOrderRequest(address=address, price=50000.0, volume=0.1)

        # Act
        params = RequestConverter.convert_limit_buy_order(request)

        # Assert
        assert params["symbol"] == "BTCUSDT"  # BTC/USDT → BTCUSDT
        assert params["side"] == "BUY"
        assert params["type"] == "LIMIT"
        assert params["price"] == "50000.0"
        assert params["quantity"] == "0.1"
        assert params["timeInForce"] == "GTC"  # 기본값

    def test_convert_limit_buy_order_post_only(self):
        """Post-only 지정가 매수 주문 변환"""
        # Arrange
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="ETH",
            quote="USDT",
            timeframe="1m",
        )
        request = LimitBuyOrderRequest(
            address=address, price=3000.0, volume=1.5, post_only=True
        )

        # Act
        params = RequestConverter.convert_limit_buy_order(request)

        # Assert
        assert params["symbol"] == "ETHUSDT"
        assert params["side"] == "BUY"
        assert params["type"] == "LIMIT"
        assert params["timeInForce"] == "GTX"  # Post-only

    def test_convert_limit_sell_order_basic(self):
        """기본 지정가 매도 주문 변환"""
        # Arrange
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m",
        )
        request = LimitSellOrderRequest(address=address, price=51000.0, volume=0.05)

        # Act
        params = RequestConverter.convert_limit_sell_order(request)

        # Assert
        assert params["symbol"] == "BTCUSDT"
        assert params["side"] == "SELL"
        assert params["type"] == "LIMIT"
        assert params["price"] == "51000.0"
        assert params["quantity"] == "0.05"


class TestRequestConverterMarketOrders:
    """시장가 주문 변환 테스트"""

    def test_convert_market_buy_order(self):
        """시장가 매수 주문 변환"""
        # Arrange
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="BTC",
            quote="USDT",
            timeframe="1m",
        )
        request = MarketBuyOrderRequest(address=address, volume=0.1)

        # Act
        params = RequestConverter.convert_market_buy_order(request)

        # Assert
        assert params["symbol"] == "BTCUSDT"
        assert params["side"] == "BUY"
        assert params["type"] == "MARKET"
        assert params["quantity"] == "0.1"
        assert "price" not in params  # 시장가는 가격 없음
        assert "timeInForce" not in params  # 시장가는 timeInForce 없음

    def test_convert_market_sell_order(self):
        """시장가 매도 주문 변환"""
        # Arrange
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="ETH",
            quote="USDT",
            timeframe="1m",
        )
        request = MarketSellOrderRequest(address=address, volume=2.0)

        # Act
        params = RequestConverter.convert_market_sell_order(request)

        # Assert
        assert params["symbol"] == "ETHUSDT"
        assert params["side"] == "SELL"
        assert params["type"] == "MARKET"
        assert params["quantity"] == "2.0"


class TestRequestConverterSymbolFormat:
    """심볼 포맷 변환 테스트"""

    def test_symbol_format_conversion(self):
        """StockAddress에서 Binance 심볼 포맷으로 변환"""
        # Arrange
        address = StockAddress(
            archetype="candle",
            exchange="binance",
            tradetype="spot",
            base="BNB",
            quote="BTC",
            timeframe="1m",
        )
        request = LimitBuyOrderRequest(address=address, price=0.01, volume=10.0)

        # Act
        params = RequestConverter.convert_limit_buy_order(request)

        # Assert
        assert params["symbol"] == "BNBBTC"  # BNB/BTC → BNBBTC
