"""Tests for SpotLedger and SpotLedgerEntry."""

from financial_assets.ledger import SpotLedger, SpotLedgerEntry
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress
import pytest
import pandas as pd


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


@pytest.fixture
def buy_trade_1btc_50k(stock_address):
    """Create a BUY trade: 1.0 BTC at 50000 USDT."""
    return SpotTrade(
        stock_address=stock_address,
        trade_id="trade-1",
        fill_id="fill-1",
        side=SpotSide.BUY,
        pair=Pair(Token("BTC", 1.0), Token("USDT", 50000.0)),
        timestamp=1234567890,
    )


@pytest.fixture
def buy_trade_half_btc_52k(stock_address):
    """Create a BUY trade: 0.5 BTC at 52000 USDT (26000 total)."""
    return SpotTrade(
        stock_address=stock_address,
        trade_id="trade-2",
        fill_id="fill-2",
        side=SpotSide.BUY,
        pair=Pair(Token("BTC", 0.5), Token("USDT", 26000.0)),
        timestamp=1234567900,
    )


@pytest.fixture
def sell_trade_half_btc_55k(stock_address):
    """Create a SELL trade: 0.5 BTC at 55000 USDT (27500 total)."""
    return SpotTrade(
        stock_address=stock_address,
        trade_id="trade-3",
        fill_id="fill-3",
        side=SpotSide.SELL,
        pair=Pair(Token("BTC", 0.5), Token("USDT", 27500.0)),
        timestamp=1234567910,
    )


class TestSpotLedgerEntry:
    """Test cases for SpotLedgerEntry dataclass."""

    def test_entry_creation(self, buy_trade_1btc_50k):
        """Test basic SpotLedgerEntry creation."""
        entry = SpotLedgerEntry(
            timestamp=1234567890,
            trade=buy_trade_1btc_50k,
            asset_change=1.0,
            value_change=-50000.0,
            cumulative_asset=1.0,
            cumulative_value=-50000.0,
            average_price=50000.0,
            realized_pnl=None,
        )

        assert entry.timestamp == 1234567890
        assert entry.trade == buy_trade_1btc_50k
        assert entry.asset_change == 1.0
        assert entry.value_change == -50000.0
        assert entry.cumulative_asset == 1.0
        assert entry.cumulative_value == -50000.0
        assert entry.average_price == 50000.0
        assert entry.realized_pnl is None

    def test_entry_immutability(self, buy_trade_1btc_50k):
        """Test that SpotLedgerEntry is immutable (frozen dataclass)."""
        entry = SpotLedgerEntry(
            timestamp=1234567890,
            trade=buy_trade_1btc_50k,
            asset_change=1.0,
            value_change=-50000.0,
            cumulative_asset=1.0,
            cumulative_value=-50000.0,
            average_price=50000.0,
            realized_pnl=None,
        )

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            entry.cumulative_asset = 2.0

    def test_entry_with_realized_pnl(self, sell_trade_half_btc_55k):
        """Test SpotLedgerEntry with realized PnL (SELL trade)."""
        entry = SpotLedgerEntry(
            timestamp=1234567910,
            trade=sell_trade_half_btc_55k,
            asset_change=-0.5,
            value_change=27500.0,
            cumulative_asset=0.5,
            cumulative_value=-22500.0,
            average_price=50000.0,
            realized_pnl=2500.0,  # (55000 - 50000) * 0.5
        )

        assert entry.realized_pnl == 2500.0
        assert entry.asset_change == -0.5
        assert entry.value_change == 27500.0

    def test_entry_timestamp_field(self, buy_trade_1btc_50k):
        """Test that SpotLedgerEntry has timestamp field."""
        entry = SpotLedgerEntry(
            timestamp=9999999999,
            trade=buy_trade_1btc_50k,
            asset_change=1.0,
            value_change=-50000.0,
            cumulative_asset=1.0,
            cumulative_value=-50000.0,
            average_price=50000.0,
            realized_pnl=None,
        )

        assert entry.timestamp == 9999999999

    def test_entry_string_representation(self, buy_trade_1btc_50k):
        """Test __str__ and __repr__ methods."""
        entry = SpotLedgerEntry(
            timestamp=1234567890,
            trade=buy_trade_1btc_50k,
            asset_change=1.0,
            value_change=-50000.0,
            cumulative_asset=1.0,
            cumulative_value=-50000.0,
            average_price=50000.0,
            realized_pnl=None,
        )

        entry_str = str(entry)
        assert "1234567890" in entry_str
        assert "BUY" in entry_str
        assert "50000" in entry_str

        entry_repr = repr(entry)
        assert "SpotLedgerEntry" in entry_repr


class TestSpotLedger:
    """Test cases for SpotLedger class."""

    def test_ledger_initialization(self):
        """Test SpotLedger initialization."""
        ledger = SpotLedger(ticker="BTC-USDT")

        assert ledger.ticker == "BTC-USDT"

    def test_empty_ledger_to_dataframe(self):
        """Test that empty ledger returns empty DataFrame."""
        ledger = SpotLedger(ticker="BTC-USDT")
        df = ledger.to_dataframe()

        assert len(df) == 0
        assert "timestamp" in df.columns
        assert "side" in df.columns
        assert "asset_change" in df.columns
        assert "value_change" in df.columns
        assert "cumulative_asset" in df.columns
        assert "cumulative_value" in df.columns
        assert "average_price" in df.columns
        assert "realized_pnl" in df.columns

    def test_add_buy_trade(self, buy_trade_1btc_50k):
        """Test adding a BUY trade (position building)."""
        ledger = SpotLedger(ticker="BTC-USDT")
        entry = ledger.add_trade(buy_trade_1btc_50k)

        assert entry.timestamp == 1234567890
        assert entry.asset_change == 1.0
        assert entry.value_change == -50000.0
        assert entry.cumulative_asset == 1.0
        assert entry.cumulative_value == -50000.0
        assert entry.average_price == 50000.0
        assert entry.realized_pnl is None

    def test_add_sell_trade(self, buy_trade_1btc_50k, sell_trade_half_btc_55k):
        """Test adding a SELL trade (position reduction + PnL)."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)
        entry = ledger.add_trade(sell_trade_half_btc_55k)

        # PnL: (55000 - 50000) * 0.5 = 2500
        assert entry.realized_pnl == 2500.0
        assert entry.asset_change == -0.5
        assert entry.cumulative_asset == 0.5
        assert entry.average_price == 50000.0  # Average price stays same

    def test_average_price_calculation_multiple_buys(
        self, buy_trade_1btc_50k, buy_trade_half_btc_52k
    ):
        """Test weighted average price calculation across multiple buys."""
        ledger = SpotLedger(ticker="BTC-USDT")

        # First buy: 1.0 BTC at 50000
        ledger.add_trade(buy_trade_1btc_50k)

        # Second buy: 0.5 BTC at 52000
        # Average price: (50000 * 1.0 + 52000 * 0.5) / 1.5 = 50666.67
        entry2 = ledger.add_trade(buy_trade_half_btc_52k)

        assert entry2.cumulative_asset == 1.5
        assert abs(entry2.average_price - 50666.67) < 0.01

    def test_realized_pnl_calculation(self, buy_trade_1btc_50k, stock_address):
        """Test realized PnL calculation on SELL."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)

        # Sell 0.6 BTC at 55000 (33000 total)
        sell_trade = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-sell",
            fill_id="fill-sell",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 0.6), Token("USDT", 33000.0)),
            timestamp=1234567920,
        )
        entry = ledger.add_trade(sell_trade)

        # PnL: (55000 - 50000) * 0.6 = 3000
        assert entry.realized_pnl == 3000.0
        assert entry.cumulative_asset == 0.4

    def test_to_dataframe_with_entries(
        self, buy_trade_1btc_50k, sell_trade_half_btc_55k
    ):
        """Test to_dataframe() with multiple entries."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)
        ledger.add_trade(sell_trade_half_btc_55k)

        df = ledger.to_dataframe()

        assert len(df) == 2
        assert df.iloc[0]["timestamp"] == 1234567890
        assert df.iloc[0]["side"] == "buy"
        assert df.iloc[0]["cumulative_asset"] == 1.0
        assert df.iloc[1]["timestamp"] == 1234567910
        assert df.iloc[1]["side"] == "sell"
        assert df.iloc[1]["realized_pnl"] == 2500.0

    def test_dataframe_column_names(self):
        """Test DataFrame column names and structure."""
        ledger = SpotLedger(ticker="BTC-USDT")
        df = ledger.to_dataframe()

        expected_columns = [
            "timestamp",
            "side",
            "asset_change",
            "value_change",
            "cumulative_asset",
            "cumulative_value",
            "average_price",
            "realized_pnl",
        ]
        assert list(df.columns) == expected_columns

    def test_dataframe_chronological_order(
        self, buy_trade_1btc_50k, sell_trade_half_btc_55k
    ):
        """Test that DataFrame maintains chronological order."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)
        ledger.add_trade(sell_trade_half_btc_55k)

        df = ledger.to_dataframe()

        assert df.iloc[0]["timestamp"] < df.iloc[1]["timestamp"]

    def test_position_complete_closure(self, buy_trade_1btc_50k, stock_address):
        """Test complete position closure and average price reset."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)

        # Sell entire position: 1.0 BTC at 55000
        sell_all = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-sell-all",
            fill_id="fill-sell-all",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 1.0), Token("USDT", 55000.0)),
            timestamp=1234567930,
        )
        entry = ledger.add_trade(sell_all)

        assert entry.cumulative_asset == 0.0
        assert entry.realized_pnl == 5000.0  # (55000 - 50000) * 1.0

        # Check DataFrame
        df = ledger.to_dataframe()
        assert df.iloc[-1]["cumulative_asset"] == 0.0

    def test_position_closure_resets_average_price(
        self, buy_trade_1btc_50k, stock_address
    ):
        """Test that average price is reset after complete position closure."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)

        # Sell entire position
        sell_all = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-sell-all",
            fill_id="fill-sell-all",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 1.0), Token("USDT", 55000.0)),
            timestamp=1234567930,
        )
        ledger.add_trade(sell_all)

        # After full liquidation, internal average price should be None
        assert ledger._average_price is None
        assert ledger._cumulative_asset == 0.0

    def test_buy_after_position_closure(self, buy_trade_1btc_50k, stock_address):
        """Test buying again after complete position closure."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)

        # Sell entire position
        sell_all = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-sell-all",
            fill_id="fill-sell-all",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 1.0), Token("USDT", 55000.0)),
            timestamp=1234567930,
        )
        ledger.add_trade(sell_all)

        # Buy again at different price
        buy_again = SpotTrade(
            stock_address=stock_address,
            trade_id="trade-buy-again",
            fill_id="fill-buy-again",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 2.0), Token("USDT", 120000.0)),
            timestamp=1234567940,
        )
        entry = ledger.add_trade(buy_again)

        # New average price should be fresh (60000)
        assert entry.average_price == 60000.0
        assert entry.cumulative_asset == 2.0

    def test_ledger_string_representation(self, buy_trade_1btc_50k):
        """Test __str__ and __repr__ methods of SpotLedger."""
        ledger = SpotLedger(ticker="BTC-USDT")
        ledger.add_trade(buy_trade_1btc_50k)

        ledger_str = str(ledger)
        assert "BTC-USDT" in ledger_str
        assert "entries" in ledger_str.lower() or "1" in ledger_str

        ledger_repr = repr(ledger)
        assert "SpotLedger" in ledger_repr
        assert "BTC-USDT" in ledger_repr

    def test_zero_position_edge_case(self, stock_address):
        """Test edge case with very small floating point values."""
        ledger = SpotLedger(ticker="BTC-USDT")

        # Buy 0.00000001 BTC
        tiny_buy = SpotTrade(
            stock_address=stock_address,
            trade_id="tiny-buy",
            fill_id="fill-tiny-buy",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 0.00000001), Token("USDT", 0.0005)),
            timestamp=1234567890,
        )
        ledger.add_trade(tiny_buy)

        # Sell exact same amount
        tiny_sell = SpotTrade(
            stock_address=stock_address,
            trade_id="tiny-sell",
            fill_id="fill-tiny-sell",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 0.00000001), Token("USDT", 0.0006)),
            timestamp=1234567900,
        )
        entry = ledger.add_trade(tiny_sell)

        # Position should be closed (within floating point tolerance)
        assert entry.cumulative_asset == 0.0
        assert ledger._average_price is None
