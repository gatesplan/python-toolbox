"""Tests for WalletInspector."""

import pytest
from financial_assets.wallet import SpotWallet, WalletInspector, WalletWorker
from financial_assets.trade import SpotTrade
from financial_assets.order import SpotOrder
from financial_assets.constants import OrderSide
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price


def create_spot_trade(trade_id, side, asset_amount, value_amount, asset_symbol="BTC", value_symbol="USD", stock_address=None, timestamp=1234567890):
    """Helper to create SpotTrade."""
    if stock_address is None:
        stock_address = StockAddress("crypto", "binance", "spot", asset_symbol.lower(), value_symbol.lower(), "1d")
    price = value_amount / asset_amount if asset_amount > 0 else 0.0
    order = SpotOrder(f"order-{trade_id}", stock_address, side, "limit", price, asset_amount, timestamp)
    pair = Pair(Token(asset_symbol, asset_amount), Token(value_symbol, value_amount))
    return SpotTrade(trade_id, order, pair, timestamp)


@pytest.fixture
def stock_address_btc_usd():
    """BTC-USD stock address."""
    return StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")


@pytest.fixture
def stock_address_eth_usd():
    """ETH-USD stock address."""
    return StockAddress("crypto", "binance", "spot", "eth", "usd", "1d")


class TestWalletInspectorInitialization:
    """Test WalletInspector initialization."""

    def test_initialization(self):
        """Test inspector initialization."""
        wallet = SpotWallet()
        inspector = WalletInspector(wallet)

        assert inspector.wallet is wallet


class TestTotalValue:
    """Test total value calculation."""

    def test_total_value_currency_only(self):
        """Test total value with currency only."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=50000.0)
        wallet.deposit_currency(symbol="KRW", amount=1000000.0)

        inspector = WalletInspector(wallet)

        # USD only (KRW ignored)
        total = inspector.get_total_value(quote_symbol="USD", current_prices={})
        assert total == 50000.0

    def test_total_value_with_assets(self, stock_address_btc_usd):
        """Test total value with assets."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BUY 1.0 BTC at 50000
        trade = create_spot_trade(
            trade_id="t1",
            side=OrderSide.BUY,
            asset_amount=1.0,
            value_amount=50000.0,
            asset_symbol="BTC",
            value_symbol="USD",
            stock_address=stock_address_btc_usd,
            timestamp=1234567890,
        )
        wallet.process_trade(trade)

        inspector = WalletInspector(wallet)

        # Current price: 55000
        btc_price = Price(
            exchange="binance",
            market="BTC/USD",
            t=1234567900,
            h=56000.0,
            l=54000.0,
            o=54500.0,
            c=55000.0,
            v=1000.0,
        )

        # USD: 50000, BTC: 1.0 * 55000 = 55000, Total: 105000
        total = inspector.get_total_value("USD", {"BTC-USD": btc_price})
        assert total == 105000.0

    def test_total_value_multiple_assets(
        self, stock_address_btc_usd, stock_address_eth_usd
    ):
        """Test total value with multiple assets."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BTC
        wallet.process_trade(
            create_spot_trade(
                trade_id="t1",
                side=OrderSide.BUY,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567890,
            )
        )

        # ETH
        wallet.process_trade(
            create_spot_trade(
                trade_id="t2",
                side=OrderSide.BUY,
                asset_amount=10.0,
                value_amount=20000.0,
                asset_symbol="ETH",
                value_symbol="USD",
                stock_address=stock_address_eth_usd,
                timestamp=1234567900,
            )
        )

        inspector = WalletInspector(wallet)

        btc_price = Price("binance", "BTC/USD", 1234567910, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)
        eth_price = Price("binance", "ETH/USD", 1234567910, 2600.0, 2400.0, 2450.0, 2500.0, 5000.0)

        # USD: 30000, BTC: 55000, ETH: 25000 = 110000
        total = inspector.get_total_value(
            "USD", {"BTC-USD": btc_price, "ETH-USD": eth_price}
        )
        assert total == 110000.0


class TestRealizedPnL:
    """Test realized PnL calculation."""

    def test_total_realized_pnl(self, stock_address_btc_usd):
        """Test total realized PnL."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BUY
        wallet.process_trade(
            create_spot_trade(
                trade_id="t1",
                side=OrderSide.BUY,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567890,
            )
        )

        # SELL
        wallet.process_trade(
            create_spot_trade(
                trade_id="t2",
                side=OrderSide.SELL,
                asset_amount=0.6,
                value_amount=33000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567900,
            )
        )

        inspector = WalletInspector(wallet)

        # Realized PnL: (55000 - 50000) * 0.6 = 3000
        total_pnl = inspector.get_total_realized_pnl()
        assert total_pnl == 3000.0

    def test_multiple_pairs_realized_pnl(
        self, stock_address_btc_usd, stock_address_eth_usd
    ):
        """Test realized PnL from multiple trading pairs."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=200000.0)

        # BTC: Buy-Sell
        wallet.process_trade(
            create_spot_trade(
                trade_id="t1",
                side=OrderSide.BUY,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567890,
            )
        )
        wallet.process_trade(
            create_spot_trade(
                trade_id="t2",
                side=OrderSide.SELL,
                asset_amount=0.5,
                value_amount=27500.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567900,
            )
        )

        # ETH: Buy-Sell
        wallet.process_trade(
            create_spot_trade(
                trade_id="t3",
                side=OrderSide.BUY,
                asset_amount=10.0,
                value_amount=20000.0,
                asset_symbol="ETH",
                value_symbol="USD",
                stock_address=stock_address_eth_usd,
                timestamp=1234567910,
            )
        )
        wallet.process_trade(
            create_spot_trade(
                trade_id="t4",
                side=OrderSide.SELL,
                asset_amount=5.0,
                value_amount=11000.0,
                asset_symbol="ETH",
                value_symbol="USD",
                stock_address=stock_address_eth_usd,
                timestamp=1234567920,
            )
        )

        inspector = WalletInspector(wallet)

        # BTC PnL: (55000 - 50000) * 0.5 = 2500
        # ETH PnL: (2200 - 2000) * 5 = 1000
        # Total: 3500
        total_pnl = inspector.get_total_realized_pnl()
        assert total_pnl == 3500.0


class TestUnrealizedPnL:
    """Test unrealized PnL calculation."""

    def test_unrealized_pnl(self, stock_address_btc_usd):
        """Test unrealized PnL."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BUY 1.0 BTC at 50000
        wallet.process_trade(
            create_spot_trade(
                trade_id="t1",
                side=OrderSide.BUY,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567890,
            )
        )

        inspector = WalletInspector(wallet)

        btc_price = Price("binance", "BTC/USD", 1234567900, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)

        # (55000 - 50000) * 1.0 = 5000
        unrealized = inspector.get_unrealized_pnl("USD", {"BTC-USD": btc_price})
        assert unrealized == 5000.0

    def test_unrealized_pnl_multiple_assets(
        self, stock_address_btc_usd, stock_address_eth_usd
    ):
        """Test unrealized PnL with multiple assets."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BTC: 1.0 at 50000
        wallet.process_trade(
            create_spot_trade(
                trade_id="t1",
                side=OrderSide.BUY,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567890,
            )
        )

        # ETH: 10.0 at 20000
        wallet.process_trade(
            create_spot_trade(
                trade_id="t2",
                side=OrderSide.BUY,
                asset_amount=10.0,
                value_amount=20000.0,
                asset_symbol="ETH",
                value_symbol="USD",
                stock_address=stock_address_eth_usd,
                timestamp=1234567900,
            )
        )

        inspector = WalletInspector(wallet)

        btc_price = Price("binance", "BTC/USD", 1234567910, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)
        eth_price = Price("binance", "ETH/USD", 1234567910, 1900.0, 1700.0, 1750.0, 1800.0, 10000.0)

        # BTC: (55000 - 50000) * 1.0 = 5000
        # ETH: (1800 - 2000) * 10.0 = -2000
        # Total: 3000
        unrealized = inspector.get_unrealized_pnl(
            "USD", {"BTC-USD": btc_price, "ETH-USD": eth_price}
        )
        assert unrealized == 3000.0


class TestPositionSummary:
    """Test position summary DataFrame."""

    def test_position_summary(self, stock_address_btc_usd, stock_address_eth_usd):
        """Test position summary DataFrame."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=200000.0)

        # BTC
        wallet.process_trade(
            create_spot_trade(
                trade_id="t1",
                side=OrderSide.BUY,
                asset_amount=1.0,
                value_amount=50000.0,
                asset_symbol="BTC",
                value_symbol="USD",
                stock_address=stock_address_btc_usd,
                timestamp=1234567890,
            )
        )

        # ETH
        wallet.process_trade(
            create_spot_trade(
                trade_id="t2",
                side=OrderSide.BUY,
                asset_amount=10.0,
                value_amount=20000.0,
                asset_symbol="ETH",
                value_symbol="USD",
                stock_address=stock_address_eth_usd,
                timestamp=1234567900,
            )
        )

        inspector = WalletInspector(wallet)

        btc_price = Price("binance", "BTC/USD", 1234567910, 56000.0, 54000.0, 54500.0, 55000.0, 1000.0)
        eth_price = Price("binance", "ETH/USD", 1234567910, 1900.0, 1700.0, 1750.0, 1800.0, 10000.0)

        df = inspector.get_position_summary("USD", {"BTC-USD": btc_price, "ETH-USD": eth_price})

        # Check columns
        assert "ticker" in df.columns
        assert "asset_amount" in df.columns
        assert "avg_price" in df.columns
        assert "cost_basis" in df.columns
        assert "current_value" in df.columns
        assert "unrealized_pnl" in df.columns

        # Check BTC row
        btc_row = df[df["ticker"] == "BTC-USD"].iloc[0]
        assert btc_row["asset_amount"] == 1.0
        assert btc_row["avg_price"] == 50000.0
        assert btc_row["cost_basis"] == 50000.0
        assert btc_row["current_value"] == 55000.0
        assert btc_row["unrealized_pnl"] == 5000.0

        # Check ETH row
        eth_row = df[df["ticker"] == "ETH-USD"].iloc[0]
        assert eth_row["asset_amount"] == 10.0
        assert eth_row["avg_price"] == 2000.0
        assert eth_row["unrealized_pnl"] == -2000.0


class TestCurrencySummary:
    """Test currency summary DataFrame."""

    def test_currency_summary(self):
        """Test currency summary DataFrame."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=50000.0)
        wallet.deposit_currency(symbol="KRW", amount=1000000.0)

        inspector = WalletInspector(wallet)

        df = inspector.get_currency_summary()

        # Check columns
        assert "symbol" in df.columns
        assert "amount" in df.columns

        # Check USD row
        usd_row = df[df["symbol"] == "USD"].iloc[0]
        assert usd_row["amount"] == 50000.0

        # Check KRW row
        krw_row = df[df["symbol"] == "KRW"].iloc[0]
        assert krw_row["amount"] == 1000000.0


class TestCustomWorker:
    """Test custom worker extension."""

    def test_custom_worker(self):
        """Test creating and using a custom worker."""

        class CustomAnalysisWorker(WalletWorker):
            def analyze(self, wallet: SpotWallet) -> dict:
                return {
                    "currency_count": len(wallet.list_currencies()),
                    "ticker_count": len(wallet.list_tickers()),
                }

        wallet = SpotWallet()
        wallet.deposit_currency("USD", 10000.0)

        worker = CustomAnalysisWorker()
        result = worker.analyze(wallet)

        assert "currency_count" in result
        assert "ticker_count" in result
        assert result["currency_count"] == 1
        assert result["ticker_count"] == 0


class TestStringRepresentations:
    """Test string representations."""

    def test_str_representation(self):
        """Test __str__ method."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=10000.0)

        inspector = WalletInspector(wallet)

        inspector_str = str(inspector)
        assert "WalletInspector" in inspector_str or "inspector" in inspector_str.lower()

    def test_repr_representation(self):
        """Test __repr__ method."""
        wallet = SpotWallet()
        inspector = WalletInspector(wallet)

        inspector_repr = repr(inspector)
        assert "WalletInspector" in inspector_repr
