"""Tests for Order module."""

import pytest
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.stock_address import StockAddress
from financial_assets.token import Token
from financial_assets.pair import Pair


@pytest.fixture
def stock_address():
    """Create a sample stock address for testing."""
    return StockAddress(
        archetype="crypto",
        exchange="binance",
        tradetype="spot",
        base="btc",
        quote="usdt",
        timeframe="1d",
    )


class TestSpotOrderCreation:
    """Test order creation with different types."""

    def test_limit_order_creation(self, stock_address):
        """Test creating a limit order."""
        order = SpotOrder(
            order_id="order-123",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        assert order.order_id == "order-123"
        assert order.side == SpotSide.BUY
        assert order.order_type == "limit"
        assert order.price == 50000.0
        assert order.amount == 1.0
        assert order.filled_amount == 0.0
        assert order.status == "pending"
        assert order.stop_price is None

    def test_market_order_creation(self, stock_address):
        """Test creating a market order with price=None."""
        order = SpotOrder(
            order_id="market-order-1",
            stock_address=stock_address,
            side=SpotSide.SELL,
            order_type="market",
            price=None,
            amount=0.5,
            timestamp=1234567900,
        )

        assert order.price is None
        assert order.order_type == "market"

    def test_stop_order_creation(self, stock_address):
        """Test creating a stop order with stop_price."""
        order = SpotOrder(
            order_id="stop-order-1",
            stock_address=stock_address,
            side=SpotSide.SELL,
            order_type="stop",
            price=45000.0,
            amount=0.3,
            timestamp=1234567910,
            stop_price=48000.0,
        )

        assert order.stop_price == 48000.0
        assert order.order_type == "stop"


class TestFillByAssetAmount:
    """Test fill_by_asset_amount method."""

    def test_partial_fill_by_asset_amount(self, stock_address):
        """Test partial fill using asset amount."""
        order = SpotOrder(
            order_id="order-partial",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        trade = order.fill_by_asset_amount(
            amount=0.3, price=50100.0, timestamp=1234567900
        )

        # Verify Trade object
        assert isinstance(trade, SpotTrade)
        assert trade.trade_id == "order-partial"
        assert trade.side == SpotSide.BUY
        assert trade.pair.get_asset() == 0.3
        assert trade.pair.get_value() == 0.3 * 50100.0
        assert trade.timestamp == 1234567900

        # Verify Order state
        assert order.filled_amount == 0.3
        assert order.status == "partial"
        assert order.remaining_asset() == pytest.approx(0.7)

    def test_full_fill_by_asset_amount(self, stock_address):
        """Test complete fill using asset amount."""
        order = SpotOrder(
            order_id="order-full",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        trade = order.fill_by_asset_amount(
            amount=1.0, price=50050.0, timestamp=1234567900
        )

        assert trade.pair.get_asset() == 1.0
        assert order.filled_amount == 1.0
        assert order.status == "filled"
        assert order.remaining_asset() == pytest.approx(0.0)
        assert order.is_filled() is True

    def test_multiple_partial_fills(self, stock_address):
        """Test multiple partial fills."""
        order = SpotOrder(
            order_id="order-multi",
            stock_address=stock_address,
            side=SpotSide.SELL,
            order_type="limit",
            price=51000.0,
            amount=2.0,
            timestamp=1234567890,
        )

        # First fill: 0.5 BTC
        trade1 = order.fill_by_asset_amount(0.5, 51000.0, 1234567900)
        assert order.filled_amount == 0.5
        assert order.status == "partial"

        # Second fill: 0.8 BTC
        trade2 = order.fill_by_asset_amount(0.8, 51000.0, 1234567910)
        assert order.filled_amount == 1.3
        assert order.status == "partial"

        # Third fill: 0.7 BTC (complete)
        trade3 = order.fill_by_asset_amount(0.7, 51000.0, 1234567920)
        assert order.filled_amount == 2.0
        assert order.status == "filled"
        assert order.is_filled() is True


class TestFillByValueAmount:
    """Test fill_by_value_amount method."""

    def test_partial_fill_by_value_amount(self, stock_address):
        """Test partial fill using value amount."""
        order = SpotOrder(
            order_id="order-value",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        trade = order.fill_by_value_amount(
            amount=15000.0, price=50000.0, timestamp=1234567900
        )

        # 15000 USDT = 0.3 BTC at 50000
        assert trade.pair.get_asset() == 0.3
        assert trade.pair.get_value() == 15000.0
        assert order.filled_amount == 0.3
        assert order.status == "partial"

    def test_full_fill_by_value_amount(self, stock_address):
        """Test complete fill using value amount."""
        order = SpotOrder(
            order_id="order-value-full",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        trade = order.fill_by_value_amount(
            amount=50000.0, price=50000.0, timestamp=1234567900
        )

        assert trade.pair.get_asset() == 1.0
        assert order.is_filled() is True

    def test_fill_by_value_amount_zero_price_raises_error(self, stock_address):
        """Test that zero price raises ValueError."""
        order = SpotOrder(
            order_id="order-zero-price",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="Price cannot be zero"):
            order.fill_by_value_amount(amount=1000.0, price=0.0, timestamp=1234567900)


class TestRemainingMethods:
    """Test remaining amount/rate methods."""

    def test_remaining_asset(self, stock_address):
        """Test remaining_asset calculation."""
        order = SpotOrder(
            order_id="order-remain",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=2.0,
            timestamp=1234567890,
        )

        assert order.remaining_asset() == 2.0

        order.fill_by_asset_amount(0.7, 50000.0, 1234567900)
        assert order.remaining_asset() == pytest.approx(1.3)

        order.fill_by_asset_amount(1.3, 50000.0, 1234567910)
        assert order.remaining_asset() == pytest.approx(0.0)

    def test_remaining_value(self, stock_address):
        """Test remaining_value calculation."""
        order = SpotOrder(
            order_id="order-remain-value",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        # Initial remaining_value = 1.0 * 50000.0 = 50000.0
        assert order.remaining_value() == 50000.0

        # After filling 0.3 BTC
        order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
        # remaining = 0.7 * 50000.0 = 35000.0
        assert order.remaining_value() == pytest.approx(35000.0)

    def test_remaining_value_market_order_raises_error(self, stock_address):
        """Test that remaining_value raises error for market orders."""
        order = SpotOrder(
            order_id="market-order",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="market",
            price=None,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="Cannot calculate remaining_value"):
            order.remaining_value()

    def test_remaining_rate(self, stock_address):
        """Test remaining_rate calculation."""
        order = SpotOrder(
            order_id="order-rate",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        # Initial state: 100% remaining
        assert order.remaining_rate() == 1.0

        # 30% filled
        order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
        assert order.remaining_rate() == pytest.approx(0.7)

        # Completely filled
        order.fill_by_asset_amount(0.7, 50000.0, 1234567910)
        assert order.remaining_rate() == pytest.approx(0.0)


class TestSpotOrderStatus:
    """Test order status management."""

    def test_status_transitions(self, stock_address):
        """Test status transitions: pending → partial → filled."""
        order = SpotOrder(
            order_id="order-status",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        # Initial status
        assert order.status == "pending"
        assert order.is_filled() is False

        # Partial fill
        order.fill_by_asset_amount(0.4, 50000.0, 1234567900)
        assert order.status == "partial"
        assert order.is_filled() is False

        # Complete fill
        order.fill_by_asset_amount(0.6, 50000.0, 1234567910)
        assert order.status == "filled"
        assert order.is_filled() is True

    def test_cancel_order(self, stock_address):
        """Test order cancellation."""
        order = SpotOrder(
            order_id="order-cancel",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        # Partial fill then cancel
        order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
        assert order.status == "partial"

        order.cancel()
        assert order.status == "canceled"

    def test_cannot_fill_canceled_order(self, stock_address):
        """Test that canceled orders cannot be filled."""
        order = SpotOrder(
            order_id="order-canceled",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        order.cancel()

        with pytest.raises(ValueError, match="Cannot fill a canceled order"):
            order.fill_by_asset_amount(0.1, 50000.0, 1234567920)


class TestTradeFactory:
    """Test Trade object creation from Order fills."""

    def test_trade_object_validation(self, stock_address):
        """Test that fill methods create valid Trade objects."""
        order = SpotOrder(
            order_id="order-factory",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        trade = order.fill_by_asset_amount(0.5, 50100.0, 1234567900)

        # Verify Trade properties
        assert isinstance(trade, SpotTrade)
        assert trade.stock_address == stock_address
        assert trade.trade_id == "order-factory"
        assert trade.side == SpotSide.BUY
        assert trade.timestamp == 1234567900

        # Verify Pair
        assert isinstance(trade.pair, Pair)
        assert trade.pair.get_asset() == 0.5
        assert trade.pair.get_value() == 0.5 * 50100.0
        assert trade.pair.get_asset_token().symbol == stock_address.base
        assert trade.pair.get_value_token().symbol == stock_address.quote

    def test_sell_order_trade_creation(self, stock_address):
        """Test Trade creation from SELL order."""
        order = SpotOrder(
            order_id="sell-order",
            stock_address=stock_address,
            side=SpotSide.SELL,
            order_type="limit",
            price=51000.0,
            amount=2.0,
            timestamp=1234567890,
        )

        trade = order.fill_by_asset_amount(1.0, 51000.0, 1234567900)

        assert trade.side == SpotSide.SELL
        assert trade.pair.get_asset() == 1.0
        assert trade.pair.get_value() == 51000.0


class TestErrorHandling:
    """Test error handling for invalid operations."""

    def test_fill_exceeds_remaining_asset(self, stock_address):
        """Test that exceeding remaining amount raises error."""
        order = SpotOrder(
            order_id="order-exceed",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="exceeds remaining amount"):
            order.fill_by_asset_amount(1.5, 50000.0, 1234567900)

    def test_fill_exceeds_remaining_value(self, stock_address):
        """Test that exceeding remaining value raises error."""
        order = SpotOrder(
            order_id="order-exceed-value",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="exceeds remaining amount"):
            order.fill_by_value_amount(60000.0, 50000.0, 1234567900)

    def test_negative_fill_amount_raises_error(self, stock_address):
        """Test that negative fill amount raises error."""
        order = SpotOrder(
            order_id="order-negative",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="cannot be negative"):
            order.fill_by_asset_amount(-0.1, 50000.0, 1234567900)


class TestStringRepresentation:
    """Test string representations."""

    def test_str_representation(self, stock_address):
        """Test readable string output."""
        order = SpotOrder(
            order_id="order-str",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        order_str = str(order)
        assert "order-str" in order_str
        assert "BUY" in order_str
        assert "50000" in order_str or "50000.0" in order_str

    def test_repr_representation(self, stock_address):
        """Test detailed string representation."""
        order = SpotOrder(
            order_id="order-repr",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        order_repr = repr(order)
        assert "Order" in order_repr
        assert "order-repr" in order_repr
