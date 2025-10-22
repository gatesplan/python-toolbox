"""Tests for TradeFactory"""

import pytest
from financial_simulation.tradesim import TradeFactory
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotSide
from financial_assets.stock_address import StockAddress


class TestTradeFactory:
    """TradeFactory 테스트"""

    def test_create_spot_trade_with_fee(self):
        """수수료가 포함된 Trade 생성"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.001  # 0.1% 수수료
        )

        factory = TradeFactory()
        trade = factory.create_spot_trade(
            order, SpotSide.BUY, 1.0, 50000.0, 1, 1234567890
        )

        # Trade 기본 정보 확인
        assert trade.side == SpotSide.BUY
        assert trade.pair.get_asset() == 1.0
        assert trade.pair.get_value() == 50000.0

        # 수수료 확인
        assert trade.fee is not None
        assert trade.fee.symbol == "USD"
        assert trade.fee.amount == 50.0  # 50000 * 0.001

    def test_create_spot_trade_without_fee(self):
        """수수료가 없는 Trade 생성"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.0  # 수수료 없음
        )

        factory = TradeFactory()
        trade = factory.create_spot_trade(
            order, SpotSide.BUY, 1.0, 50000.0, 1, 1234567890
        )

        # 수수료 확인
        assert trade.fee is None

    def test_create_spot_trades_from_amounts(self):
        """여러 Trade 생성 시 각각 수수료 계산"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-3",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=3.0,
            timestamp=1234567890,
            fee_rate=0.001
        )

        factory = TradeFactory()
        trades = factory.create_spot_trades_from_amounts(
            order, SpotSide.BUY, [1.0, 1.5, 0.5], 50000.0, 1234567890
        )

        assert len(trades) == 3

        # 첫 번째 Trade: 1.0 BTC
        assert trades[0].pair.get_asset() == 1.0
        assert trades[0].fee.amount == 50.0  # 50000 * 0.001

        # 두 번째 Trade: 1.5 BTC
        assert trades[1].pair.get_asset() == 1.5
        assert trades[1].fee.amount == 75.0  # 75000 * 0.001

        # 세 번째 Trade: 0.5 BTC
        assert trades[2].pair.get_asset() == 0.5
        assert trades[2].fee.amount == 25.0  # 25000 * 0.001

    def test_fill_id_sequence(self):
        """Fill ID가 순차적으로 생성되는지 확인"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-4",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
        )

        factory = TradeFactory()
        trades = factory.create_spot_trades_from_amounts(
            order, SpotSide.BUY, [0.3, 0.3, 0.4], 50000.0, 1234567890
        )

        assert trades[0].fill_id == "order-4-fill-1"
        assert trades[1].fill_id == "order-4-fill-2"
        assert trades[2].fill_id == "order-4-fill-3"
