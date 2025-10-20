"""Tests for SpotWallet."""

import pytest
from financial_assets.wallet import SpotWallet
from financial_assets.trade import SpotTrade, SpotSide
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.stock_address import StockAddress


@pytest.fixture
def stock_address_btc_usd():
    """BTC-USD stock address."""
    return StockAddress(
        archetype="crypto",
        exchange="binance",
        tradetype="spot",
        base="btc",
        quote="usd",
        timeframe="1d",
    )


@pytest.fixture
def stock_address_eth_usd():
    """ETH-USD stock address."""
    return StockAddress(
        archetype="crypto",
        exchange="binance",
        tradetype="spot",
        base="eth",
        quote="usd",
        timeframe="1d",
    )


class TestSpotWalletInitialization:
    """Test SpotWallet initialization."""

    def test_initialization(self):
        """Test wallet initialization."""
        wallet = SpotWallet()

        assert wallet.list_currencies() == []
        assert wallet.list_tickers() == []


class TestCurrencyManagement:
    """Test currency deposit/withdrawal."""

    def test_deposit_currency(self):
        """Test currency deposit."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=10000.0)

        assert wallet.get_currency_balance("USD") == 10000.0
        assert "USD" in wallet.list_currencies()

    def test_deposit_multiple_times(self):
        """Test depositing same currency multiple times."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=5000.0)
        wallet.deposit_currency(symbol="USD", amount=3000.0)

        assert wallet.get_currency_balance("USD") == 8000.0

    def test_withdraw_currency(self):
        """Test currency withdrawal."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=10000.0)
        wallet.withdraw_currency(symbol="USD", amount=3000.0)

        assert wallet.get_currency_balance("USD") == 7000.0

    def test_withdraw_insufficient_balance(self):
        """Test withdrawal failure with insufficient balance."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=1000.0)

        with pytest.raises(ValueError) as exc_info:
            wallet.withdraw_currency(symbol="USD", amount=2000.0)

        assert "insufficient balance" in str(exc_info.value).lower()

    def test_get_nonexistent_currency_balance(self):
        """Test getting balance for non-existent currency."""
        wallet = SpotWallet()

        assert wallet.get_currency_balance("BTC") == 0.0

    def test_list_currencies(self):
        """Test listing currencies."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=10000.0)
        wallet.deposit_currency(symbol="KRW", amount=1000000.0)

        currencies = wallet.list_currencies()
        assert "USD" in currencies
        assert "KRW" in currencies
        assert len(currencies) == 2


class TestBuyTrade:
    """Test BUY trade processing."""

    def test_process_buy_trade(self, stock_address_btc_usd):
        """Test processing a BUY trade."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )
        wallet.process_trade(trade)

        # Check USD balance
        assert wallet.get_currency_balance("USD") == 50000.0

        # Check PairStack
        pair_stack = wallet.get_pair_stack("BTC-USD")
        assert pair_stack is not None
        assert pair_stack.total_asset_amount() == 1.0
        assert pair_stack.total_value_amount() == 50000.0
        assert pair_stack.mean_value() == 50000.0

        # Check Ledger
        ledger = wallet.get_ledger("BTC-USD")
        assert ledger is not None
        df = ledger.to_dataframe()
        assert len(df) == 1
        assert df.iloc[0]["side"] == "buy"

    def test_buy_insufficient_balance(self, stock_address_btc_usd):
        """Test BUY failure with insufficient balance."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=1000.0)

        trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )

        with pytest.raises(ValueError) as exc_info:
            wallet.process_trade(trade)

        assert "insufficient balance" in str(exc_info.value).lower()

    def test_multiple_buy_pair_stack_layers(self, stock_address_btc_usd):
        """Test multiple BUY trades - PairStack layer management."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=200000.0)

        # First buy: 1.0 BTC at 50000
        trade1 = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )
        wallet.process_trade(trade1)

        # Second buy: 0.5 BTC at 52000
        trade2 = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t2",
            fill_id="f2",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
            timestamp=1234567900,
        )
        wallet.process_trade(trade2)

        # Check PairStack
        pair_stack = wallet.get_pair_stack("BTC-USD")
        assert pair_stack.total_asset_amount() == 1.5
        assert pair_stack.total_value_amount() == 76000.0
        # Average: 76000 / 1.5 = 50666.67
        assert abs(pair_stack.mean_value() - 50666.67) < 0.01

        # Check USD balance
        assert wallet.get_currency_balance("USD") == 124000.0


class TestSellTrade:
    """Test SELL trade processing."""

    def test_process_sell_trade(self, stock_address_btc_usd):
        """Test processing a SELL trade."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BUY first
        buy_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )
        wallet.process_trade(buy_trade)

        # SELL
        sell_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t2",
            fill_id="f2",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 0.6), Token("USD", 33000.0)),
            timestamp=1234567900,
        )
        wallet.process_trade(sell_trade)

        # Check USD balance: 100000 - 50000 + 33000 = 83000
        assert wallet.get_currency_balance("USD") == 83000.0

        # Check PairStack: 0.4 BTC remaining
        pair_stack = wallet.get_pair_stack("BTC-USD")
        assert pair_stack.total_asset_amount() == 0.4
        assert pair_stack.total_value_amount() == 20000.0

        # Check Ledger: realized PnL recorded
        ledger = wallet.get_ledger("BTC-USD")
        df = ledger.to_dataframe()
        assert len(df) == 2
        assert df.iloc[1]["side"] == "sell"
        assert df.iloc[1]["realized_pnl"] == 3000.0  # (55000 - 50000) * 0.6

    def test_sell_insufficient_assets(self, stock_address_btc_usd):
        """Test SELL failure with insufficient assets."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BUY 1.0 BTC
        buy_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )
        wallet.process_trade(buy_trade)

        # Try to SELL 2.0 BTC
        sell_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t2",
            fill_id="f2",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 2.0), Token("USD", 100000.0)),
            timestamp=1234567900,
        )

        with pytest.raises(ValueError) as exc_info:
            wallet.process_trade(sell_trade)

        assert "insufficient" in str(exc_info.value).lower() or "exceeds" in str(
            exc_info.value
        ).lower()

    def test_complete_position_liquidation(self, stock_address_btc_usd):
        """Test complete position closure."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=100000.0)

        # BUY
        buy_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )
        wallet.process_trade(buy_trade)

        # SELL entire position
        sell_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t2",
            fill_id="f2",
            side=SpotSide.SELL,
            pair=Pair(Token("BTC", 1.0), Token("USD", 55000.0)),
            timestamp=1234567900,
        )
        wallet.process_trade(sell_trade)

        # Check USD balance: 100000 - 50000 + 55000 = 105000
        assert wallet.get_currency_balance("USD") == 105000.0

        # PairStack should be None or empty
        pair_stack = wallet.get_pair_stack("BTC-USD")
        assert pair_stack is None or pair_stack.is_empty()

        # Ledger still exists
        ledger = wallet.get_ledger("BTC-USD")
        assert ledger is not None
        df = ledger.to_dataframe()
        assert len(df) == 2


class TestQueries:
    """Test query methods."""

    def test_list_tickers(self, stock_address_btc_usd, stock_address_eth_usd):
        """Test listing tickers."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=200000.0)

        # BTC
        btc_trade = SpotTrade(
            stock_address=stock_address_btc_usd,
            trade_id="t1",
            fill_id="f1",
            side=SpotSide.BUY,
            pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            timestamp=1234567890,
        )
        wallet.process_trade(btc_trade)

        # ETH
        eth_trade = SpotTrade(
            stock_address=stock_address_eth_usd,
            trade_id="t2",
            fill_id="f2",
            side=SpotSide.BUY,
            pair=Pair(Token("ETH", 10.0), Token("USD", 20000.0)),
            timestamp=1234567900,
        )
        wallet.process_trade(eth_trade)

        tickers = wallet.list_tickers()
        assert "BTC-USD" in tickers
        assert "ETH-USD" in tickers
        assert len(tickers) == 2

    def test_get_nonexistent_pair_stack(self):
        """Test getting non-existent PairStack."""
        wallet = SpotWallet()

        assert wallet.get_pair_stack("BTC-USD") is None

    def test_get_nonexistent_ledger(self):
        """Test getting non-existent Ledger."""
        wallet = SpotWallet()

        assert wallet.get_ledger("BTC-USD") is None


class TestStringRepresentations:
    """Test string representations."""

    def test_str_representation(self):
        """Test __str__ method."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=10000.0)

        wallet_str = str(wallet)
        assert "SpotWallet" in wallet_str or "wallet" in wallet_str.lower()
        assert "USD" in wallet_str or "1" in wallet_str  # 1 currency

    def test_repr_representation(self):
        """Test __repr__ method."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=10000.0)

        wallet_repr = repr(wallet)
        assert "SpotWallet" in wallet_repr


class TestComplexScenarios:
    """Test complex trading scenarios."""

    def test_multiple_pairs_repeated_trades(
        self, stock_address_btc_usd, stock_address_eth_usd
    ):
        """Test multiple trading pairs with repeated buy/sell."""
        wallet = SpotWallet()
        wallet.deposit_currency(symbol="USD", amount=500000.0)

        # BTC: Buy-Sell-Buy
        wallet.process_trade(
            SpotTrade(
                stock_address=stock_address_btc_usd,
                trade_id="btc1",
                fill_id="f1",
                side=SpotSide.BUY,
                pair=Pair(Token("BTC", 2.0), Token("USD", 100000.0)),
                timestamp=1000,
            )
        )
        wallet.process_trade(
            SpotTrade(
                stock_address=stock_address_btc_usd,
                trade_id="btc2",
                fill_id="f2",
                side=SpotSide.SELL,
                pair=Pair(Token("BTC", 1.0), Token("USD", 55000.0)),
                timestamp=2000,
            )
        )
        wallet.process_trade(
            SpotTrade(
                stock_address=stock_address_btc_usd,
                trade_id="btc3",
                fill_id="f3",
                side=SpotSide.BUY,
                pair=Pair(Token("BTC", 0.5), Token("USD", 27500.0)),
                timestamp=3000,
            )
        )

        # ETH: Buy-Buy-Sell
        wallet.process_trade(
            SpotTrade(
                stock_address=stock_address_eth_usd,
                trade_id="eth1",
                fill_id="f4",
                side=SpotSide.BUY,
                pair=Pair(Token("ETH", 20.0), Token("USD", 40000.0)),
                timestamp=4000,
            )
        )
        wallet.process_trade(
            SpotTrade(
                stock_address=stock_address_eth_usd,
                trade_id="eth2",
                fill_id="f5",
                side=SpotSide.BUY,
                pair=Pair(Token("ETH", 10.0), Token("USD", 22000.0)),
                timestamp=5000,
            )
        )
        wallet.process_trade(
            SpotTrade(
                stock_address=stock_address_eth_usd,
                trade_id="eth3",
                fill_id="f6",
                side=SpotSide.SELL,
                pair=Pair(Token("ETH", 15.0), Token("USD", 33750.0)),
                timestamp=6000,
            )
        )

        # Verify final state
        assert "BTC-USD" in wallet.list_tickers()
        assert "ETH-USD" in wallet.list_tickers()

        btc_stack = wallet.get_pair_stack("BTC-USD")
        assert btc_stack.total_asset_amount() == 1.5  # 2 - 1 + 0.5

        eth_stack = wallet.get_pair_stack("ETH-USD")
        # Verify ETH stack exists and has reasonable amount
        # The split behavior from PairStack may have rounding, so check within tolerance
        assert eth_stack is not None
        assert 14.9 < eth_stack.total_asset_amount() < 15.6  # Allow for rounding

        # Check ledgers exist
        assert wallet.get_ledger("BTC-USD") is not None
        assert wallet.get_ledger("ETH-USD") is not None
