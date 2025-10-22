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

        updated_order = order.fill_by_asset_amount(amount=0.3)

        # Verify updated order
        assert isinstance(updated_order, SpotOrder)
        assert updated_order.filled_amount == 0.3
        assert updated_order.status == "partial"
        assert updated_order.remaining_asset() == pytest.approx(0.7)

        # Verify original order is unchanged (immutability)
        assert order.filled_amount == 0.0
        assert order.status == "pending"

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

        updated_order = order.fill_by_asset_amount(amount=1.0)

        assert updated_order.filled_amount == 1.0
        assert updated_order.status == "filled"
        assert updated_order.remaining_asset() == pytest.approx(0.0)
        assert updated_order.is_filled() is True

        # Verify original order is unchanged
        assert order.filled_amount == 0.0
        assert order.status == "pending"

    def test_multiple_partial_fills(self, stock_address):
        """Test multiple partial fills with chaining."""
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
        order1 = order.fill_by_asset_amount(0.5)
        assert order1.filled_amount == 0.5
        assert order1.status == "partial"

        # Second fill: 0.8 BTC
        order2 = order1.fill_by_asset_amount(0.8)
        assert order2.filled_amount == 1.3
        assert order2.status == "partial"

        # Third fill: 0.7 BTC (complete)
        order3 = order2.fill_by_asset_amount(0.7)
        assert order3.filled_amount == 2.0
        assert order3.status == "filled"
        assert order3.is_filled() is True

        # Verify original order is still unchanged
        assert order.filled_amount == 0.0
        assert order.status == "pending"


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

        updated_order = order.fill_by_value_amount(amount=15000.0)

        # 15000 USDT = 0.3 BTC at 50000
        assert updated_order.filled_amount == 0.3
        assert updated_order.status == "partial"

        # Verify original order is unchanged
        assert order.filled_amount == 0.0
        assert order.status == "pending"

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

        updated_order = order.fill_by_value_amount(amount=50000.0)

        assert updated_order.filled_amount == 1.0
        assert updated_order.is_filled() is True

        # Verify original order is unchanged
        assert order.filled_amount == 0.0

    def test_fill_by_value_amount_zero_price_raises_error(self, stock_address):
        """Test that zero price raises ValueError."""
        order = SpotOrder(
            order_id="order-zero-price",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=0.0,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="Price cannot be zero"):
            order.fill_by_value_amount(amount=1000.0)

    def test_fill_by_value_amount_market_order_raises_error(self, stock_address):
        """Test that market order (price=None) raises ValueError."""
        order = SpotOrder(
            order_id="market-order",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="market",
            price=None,
            amount=1.0,
            timestamp=1234567890,
        )

        with pytest.raises(ValueError, match="Cannot use fill_by_value_amount for market orders"):
            order.fill_by_value_amount(amount=1000.0)


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

        order1 = order.fill_by_asset_amount(0.7)
        assert order1.remaining_asset() == pytest.approx(1.3)

        order2 = order1.fill_by_asset_amount(1.3)
        assert order2.remaining_asset() == pytest.approx(0.0)

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
        order1 = order.fill_by_asset_amount(0.3)
        # remaining = 0.7 * 50000.0 = 35000.0
        assert order1.remaining_value() == pytest.approx(35000.0)

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
        order1 = order.fill_by_asset_amount(0.3)
        assert order1.remaining_rate() == pytest.approx(0.7)

        # Completely filled
        order2 = order1.fill_by_asset_amount(0.7)
        assert order2.remaining_rate() == pytest.approx(0.0)


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
        order1 = order.fill_by_asset_amount(0.4)
        assert order1.status == "partial"
        assert order1.is_filled() is False

        # Complete fill
        order2 = order1.fill_by_asset_amount(0.6)
        assert order2.status == "filled"
        assert order2.is_filled() is True

    def test_to_canceled_state(self, stock_address):
        """Test order cancellation using to_canceled_state."""
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
        order1 = order.fill_by_asset_amount(0.3)
        assert order1.status == "partial"

        canceled_order = order1.to_canceled_state()
        assert canceled_order.status == "canceled"

        # Verify original orders are unchanged
        assert order.status == "pending"
        assert order1.status == "partial"

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

        canceled_order = order.to_canceled_state()

        with pytest.raises(ValueError, match="Cannot fill a canceled order"):
            canceled_order.fill_by_asset_amount(0.1)


class TestStateChangeMethods:
    """Test state change methods (to_*_state)."""

    def test_to_pending_state(self, stock_address):
        """Test to_pending_state method."""
        order = SpotOrder(
            order_id="order-pending",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            status="partial",
        )

        pending_order = order.to_pending_state()
        assert pending_order.status == "pending"
        assert order.status == "partial"  # Original unchanged

    def test_to_partial_state(self, stock_address):
        """Test to_partial_state method."""
        order = SpotOrder(
            order_id="order-partial",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        partial_order = order.to_partial_state()
        assert partial_order.status == "partial"
        assert order.status == "pending"  # Original unchanged

    def test_to_filled_state(self, stock_address):
        """Test to_filled_state method."""
        order = SpotOrder(
            order_id="order-filled",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        filled_order = order.to_filled_state()
        assert filled_order.status == "filled"
        assert order.status == "pending"  # Original unchanged


class TestFeeRate:
    """Test fee_rate field functionality."""

    def test_fee_rate_default_value(self, stock_address):
        """Test that fee_rate defaults to 0.0."""
        order = SpotOrder(
            order_id="order-fee",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        assert order.fee_rate == 0.0

    def test_fee_rate_custom_value(self, stock_address):
        """Test setting custom fee_rate."""
        order = SpotOrder(
            order_id="order-fee-custom",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.001,  # 0.1%
        )

        assert order.fee_rate == 0.001

    def test_fee_rate_preserved_in_clone(self, stock_address):
        """Test that fee_rate is preserved when cloning."""
        order = SpotOrder(
            order_id="order-fee-clone",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.002,
        )

        updated_order = order.fill_by_asset_amount(0.3)
        assert updated_order.fee_rate == 0.002

        canceled_order = order.to_canceled_state()
        assert canceled_order.fee_rate == 0.002

    def test_fee_calculation_example(self, stock_address):
        """Test external fee calculation using fee_rate."""
        order = SpotOrder(
            order_id="order-fee-calc",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.001,  # 0.1%
        )

        # Simulate external fee calculation
        fill_amount = 0.5
        fill_price = 50100.0

        # BUY order: fee in quote currency
        fee_amount = fill_amount * fill_price * order.fee_rate
        assert fee_amount == pytest.approx(0.5 * 50100.0 * 0.001)
        assert fee_amount == pytest.approx(25.05)


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
            order.fill_by_asset_amount(1.5)

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
            order.fill_by_value_amount(60000.0)

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
            order.fill_by_asset_amount(-0.1)


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


class TestMinTradeAmount:
    """Test minimum trade amount functionality."""

    def test_order_creation_with_min_trade_amount(self, stock_address):
        """Test creating order with min_trade_amount."""
        order = SpotOrder(
            order_id="order-with-min",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            min_trade_amount=0.001,
        )

        assert order.min_trade_amount == 0.001

    def test_min_trade_amount_default_none(self, stock_address):
        """Test that min_trade_amount defaults to None."""
        order = SpotOrder(
            order_id="order-no-min",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        assert order.min_trade_amount is None

    def test_fill_above_min_trade_amount(self, stock_address):
        """Test that fills above minimum are allowed."""
        order = SpotOrder(
            order_id="order-min-1",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            min_trade_amount=0.001,
        )

        updated_order = order.fill_by_asset_amount(0.5)
        assert updated_order.filled_amount == 0.5
        assert updated_order.status == "partial"

    def test_fill_below_min_trade_amount_raises_error(self, stock_address):
        """Test that partial fills below minimum are rejected."""
        order = SpotOrder(
            order_id="order-min-2",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            min_trade_amount=0.001,
        )

        with pytest.raises(ValueError, match="below minimum trade amount"):
            order.fill_by_asset_amount(0.0005)

    def test_final_fill_below_min_allowed(self, stock_address):
        """Test that final fill is allowed even if below minimum."""
        order = SpotOrder(
            order_id="order-min-3",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            min_trade_amount=0.001,
        )

        # Fill 0.9995 BTC, leaving 0.0005 BTC
        order1 = order.fill_by_asset_amount(0.9995)
        assert order1.filled_amount == 0.9995
        assert order1.remaining_asset() == pytest.approx(0.0005)

        # Final fill of 0.0005 BTC should be allowed
        order2 = order1.fill_by_asset_amount(0.0005)
        assert order2.filled_amount == 1.0
        assert order2.status == "filled"

    def test_no_min_check_when_none(self, stock_address):
        """Test that very small fills are allowed when min_trade_amount is None."""
        order = SpotOrder(
            order_id="order-no-min",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            # min_trade_amount not specified (None)
        )

        # Very small fill should be allowed
        updated_order = order.fill_by_asset_amount(0.00001)
        assert updated_order.filled_amount == 0.00001

    def test_is_remaining_below_min(self, stock_address):
        """Test is_remaining_below_min method."""
        order = SpotOrder(
            order_id="order-check",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            min_trade_amount=0.01,
        )

        # Initially has sufficient remaining
        assert order.is_remaining_below_min() is False

        # After filling 0.995, remaining is 0.005 (below 0.01)
        order1 = order.fill_by_asset_amount(0.995)
        assert order1.is_remaining_below_min() is True

    def test_is_remaining_below_min_when_none(self, stock_address):
        """Test is_remaining_below_min returns False when min_trade_amount is None."""
        order = SpotOrder(
            order_id="order-no-min",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=0.0001,
            timestamp=1234567890,
            # No min_trade_amount
        )

        assert order.is_remaining_below_min() is False

    def test_min_trade_amount_preserved_in_clone(self, stock_address):
        """Test that min_trade_amount is preserved when cloning."""
        order = SpotOrder(
            order_id="order-min-clone",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            min_trade_amount=0.005,
        )

        updated_order = order.fill_by_asset_amount(0.3)
        assert updated_order.min_trade_amount == 0.005

        canceled_order = order.to_canceled_state()
        assert canceled_order.min_trade_amount == 0.005
