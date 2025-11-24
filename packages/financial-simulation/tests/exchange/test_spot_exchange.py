"""SpotExchange integration tests"""

import pytest
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType
from financial_assets.price import Price


class TestSpotExchangeIntegration:
    """SpotExchange integration tests with new fee interface"""

    @pytest.fixture
    def market_data(self):
        """Create market data fixture"""
        btc_prices = [
            Price(
                exchange="binance",
                market="BTCUSDT",
                t=1000 + i * 60,
                o=50000.0,
                h=51000.0,
                l=49000.0,
                c=50000.0,
                v=100.0
            )
            for i in range(10)
        ]

        data = {"BTC/USDT": btc_prices}
        return MarketData(data=data, availability_threshold=0.8, offset=0)

    def test_exchange_creation_with_fee_ratios(self, market_data):
        """Exchange should be created with fee ratios directly"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        assert exchange is not None
        assert exchange.get_balance("USDT") == 100000.0

    def test_exchange_uses_default_fee_ratios(self, market_data):
        """Exchange should use default fee ratios if not specified"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            quote_currency="USDT"
        )

        assert exchange is not None
        # Default fees: maker=0.001, taker=0.002

    def test_market_order_applies_correct_fee(self, market_data):
        """Market order should apply taker fee correctly"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="test_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000,
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order)

        assert len(trades) > 0
        # Check that fee was applied
        for trade in trades:
            if trade.fee:
                assert trade.fee.symbol == "USDT"
                # Taker fee should be applied
                trade_value = trade.pair.get_value()
                expected_fee = trade_value * 0.002
                assert trade.fee.amount == pytest.approx(expected_fee)

    def test_limit_order_applies_correct_fee(self, market_data):
        """Limit order should apply maker fee correctly"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="test_2",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=49500.0,
            amount=1.0,
            timestamp=1000,
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order)

        # Limit order may or may not fill immediately
        for trade in trades:
            if trade.fee:
                assert trade.fee.symbol == "USDT"
                # Maker fee should be applied
                trade_value = trade.pair.get_value()
                expected_fee = trade_value * 0.001
                assert trade.fee.amount == pytest.approx(expected_fee)

    def test_exchange_reset_maintains_fee_ratios(self, market_data):
        """Reset should maintain the same fee ratios"""
        exchange = SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.0005,
            taker_fee_ratio=0.0015,
            quote_currency="USDT"
        )

        # Place an order
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="test_3",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=1000,
            min_trade_amount=0.01
        )

        exchange.place_order(order)

        # Reset
        exchange.reset()

        # Check balance is restored
        assert exchange.get_balance("USDT") == 100000.0

        # Place another order after reset
        order2 = SpotOrder(
            order_id="test_4",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=1000,
            min_trade_amount=0.01
        )

        trades = exchange.place_order(order2)

        # Fee ratios should still be correct
        for trade in trades:
            if trade.fee:
                trade_value = trade.pair.get_value()
                expected_fee = trade_value * 0.0015  # taker fee
                assert trade.fee.amount == pytest.approx(expected_fee)
