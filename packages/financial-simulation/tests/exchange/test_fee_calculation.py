"""Fee calculation tests"""

import pytest
from financial_simulation.tradesim.Service import SpotTradeFactoryService
from financial_simulation.tradesim.InternalStruct import TradeParams
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType


class TestFeeCalculation:
    """Fee calculation core tests"""

    def test_market_order_uses_taker_fee(self):
        """Market orders should use taker fee"""
        service = SpotTradeFactoryService(maker_fee_ratio=0.001, taker_fee_ratio=0.002)

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert len(trades) == 1
        assert trades[0].fee is not None
        assert trades[0].fee.symbol == "USDT"
        # fee = 50000 * 0.002 = 100 USDT
        assert trades[0].fee.amount == 100.0

    def test_limit_order_uses_maker_fee(self):
        """Limit orders should use maker fee"""
        service = SpotTradeFactoryService(maker_fee_ratio=0.001, taker_fee_ratio=0.002)

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-2",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000000,
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert len(trades) == 1
        assert trades[0].fee is not None
        assert trades[0].fee.symbol == "USDT"
        # fee = 50000 * 0.001 = 50 USDT
        assert trades[0].fee.amount == 50.0

    def test_fee_always_in_quote_currency(self):
        """Fee should always be in quote currency"""
        service = SpotTradeFactoryService(maker_fee_ratio=0.001, taker_fee_ratio=0.002)

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "btc", "1d")
        order = SpotOrder(
            order_id="test-3",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1000000,
        )

        params_list = [
            TradeParams(fill_amount=10.0, fill_price=0.05, fill_index=1)
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert len(trades) == 1
        assert trades[0].fee is not None
        # Fee in BTC (quote currency)
        assert trades[0].fee.symbol == "BTC"
        # trade_value = 10 * 0.05 = 0.5 BTC
        # fee = 0.5 * 0.002 = 0.001 BTC
        assert trades[0].fee.amount == 0.001

    def test_multiple_fills_calculate_fee_separately(self):
        """Each fill should calculate fee separately"""
        service = SpotTradeFactoryService(maker_fee_ratio=0.001, taker_fee_ratio=0.002)

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-4",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=3.0,
            timestamp=1000000,
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1),
            TradeParams(fill_amount=1.0, fill_price=50100.0, fill_index=2),
            TradeParams(fill_amount=1.0, fill_price=50200.0, fill_index=3),
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert len(trades) == 3
        # Each trade has different fee based on its fill_price
        assert trades[0].fee.amount == 100.0   # 50000 * 0.002
        assert trades[1].fee.amount == 100.2   # 50100 * 0.002
        assert trades[2].fee.amount == 100.4   # 50200 * 0.002

    def test_zero_fee_ratio(self):
        """Zero fee ratio should result in no fee"""
        service = SpotTradeFactoryService(maker_fee_ratio=0.0, taker_fee_ratio=0.0)

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-5",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert len(trades) == 1
        assert trades[0].fee is None
