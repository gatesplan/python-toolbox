"""Tests for TradeFactoryDirector."""

import pytest
import sys
from pathlib import Path

# 패키지 루트를 sys.path에 추가 (설치 없이 테스트)
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

# financial-assets 패키지도 sys.path에 추가
financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.trade_factory.trade_factory_director import TradeFactoryDirector
from financial_simulation.tradesim.trade_params import TradeParams
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import Side


class TestTradeFactoryDirectorInitialization:
    """TradeFactoryDirector 초기화 테스트."""

    def test_director_initialization(self):
        """Director 초기화."""
        director = TradeFactoryDirector()
        assert director is not None
        assert hasattr(director, "_spot_factory")
        assert director._spot_factory is not None


class TestCreateSpotTrades:
    """create_spot_trades 메서드 테스트."""

    def test_create_single_trade(self):
        """단일 Trade 생성."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)
        ]

        trades = director.create_spot_trades(order, params_list, 1234567890)

        assert len(trades) == 1
        assert trades[0].trade_id == "order-1-fill-1"
        assert trades[0].pair.get_asset() == 1.0
        assert trades[0].pair.get_value() == 50000.0

    def test_create_multiple_trades(self):
        """여러 Trade 생성."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=3.0,
            timestamp=1234567890
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1),
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=2),
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=3),
        ]

        trades = director.create_spot_trades(order, params_list, 1234567890)

        assert len(trades) == 3
        assert trades[0].trade_id == "order-2-fill-1"
        assert trades[1].trade_id == "order-2-fill-2"
        assert trades[2].trade_id == "order-2-fill-3"

    def test_create_empty_trades(self):
        """빈 params_list로 빈 trades 반환."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-empty",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        params_list = []

        trades = director.create_spot_trades(order, params_list, 1234567890)

        assert len(trades) == 0
        assert trades == []


class TestCreateSpotTradesWithVariousPrices:
    """다양한 가격으로 Trade 생성 테스트."""

    def test_different_fill_prices(self):
        """각 체결마다 다른 가격."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-varied",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="market",
            price=None,
            amount=3.0,
            timestamp=1234567890
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1),
            TradeParams(fill_amount=1.0, fill_price=50100.0, fill_index=2),
            TradeParams(fill_amount=1.0, fill_price=50200.0, fill_index=3),
        ]

        trades = director.create_spot_trades(order, params_list, 1234567890)

        assert len(trades) == 3
        assert trades[0].pair.get_value() == 50000.0
        assert trades[1].pair.get_value() == 50100.0
        assert trades[2].pair.get_value() == 50200.0

    def test_different_fill_amounts(self):
        """각 체결마다 다른 수량."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "usdt", "1h")
        order = SpotOrder(
            order_id="order-amounts",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="limit",
            price=3000.0,
            amount=6.5,
            timestamp=1234567890
        )

        params_list = [
            TradeParams(fill_amount=2.0, fill_price=3000.0, fill_index=1),
            TradeParams(fill_amount=3.0, fill_price=3000.0, fill_index=2),
            TradeParams(fill_amount=1.5, fill_price=3000.0, fill_index=3),
        ]

        trades = director.create_spot_trades(order, params_list, 1234567890)

        assert len(trades) == 3
        assert trades[0].pair.get_asset() == 2.0
        assert trades[1].pair.get_asset() == 3.0
        assert trades[2].pair.get_asset() == 1.5


class TestCreateSpotTradesTimestamp:
    """timestamp 전달 테스트."""

    def test_timestamp_propagation(self):
        """timestamp가 모든 Trade에 전달됨."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-time",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=2.0,
            timestamp=1234567890
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1),
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=2),
        ]

        timestamp = 9876543210
        trades = director.create_spot_trades(order, params_list, timestamp)

        assert all(trade.timestamp == timestamp for trade in trades)

    def test_different_timestamps(self):
        """서로 다른 호출에서 다른 timestamp."""
        director = TradeFactoryDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-time2",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        params = [TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)]

        trades1 = director.create_spot_trades(order, params, 1111111111)
        trades2 = director.create_spot_trades(order, params, 2222222222)

        assert trades1[0].timestamp == 1111111111
        assert trades2[0].timestamp == 2222222222
