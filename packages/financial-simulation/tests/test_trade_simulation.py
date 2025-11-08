"""Tests for TradeSimulation."""

import pytest
import random
import numpy as np
import sys
from pathlib import Path

# 패키지 루트를 sys.path에 추가 (설치 없이 테스트)
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

# financial-assets 패키지도 sys.path에 추가
financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.trade_simulation import TradeSimulation
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import Side, OrderType


class TestTradeSimulationInitialization:
    """TradeSimulation 초기화 테스트."""

    def test_service_initialization(self):
        """Service 초기화."""
        sim = TradeSimulation()
        assert sim is not None
        assert hasattr(sim, "_factory_director")
        assert hasattr(sim, "_spot_director")


class TestTradeSimulationSpotLimitOrders:
    """Spot Limit 주문 처리 테스트."""

    def test_limit_buy_order(self):
        """Limit Buy 주문 전체 프로세스."""
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-buy-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.5,
            timestamp=1234567890,
            fee_rate=0.001
        )

        # body 범위에 주문 가격 포함
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        # 체결 확인
        assert len(trades) == 1
        assert trades[0].trade_id == "limit-buy-1-fill-1"
        assert trades[0].pair.get_asset() == 1.5
        assert trades[0].pair.get_value() == 75000.0  # 1.5 * 50000
        assert trades[0].timestamp == price.t

        # 수수료 확인
        assert trades[0].fee is not None
        assert trades[0].fee.amount == 75.0  # 75000 * 0.001

    def test_limit_sell_order(self):
        """Limit Sell 주문 전체 프로세스."""
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "usdt", "1h")
        order = SpotOrder(
            order_id="limit-sell-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=3000.0,
            amount=5.0,
            timestamp=1234567890,
            fee_rate=0.001
        )

        # body 범위에 주문 가격 포함
        price = Price("binance", "ETH/USDT", 1234567890, 3200, 2900, 2950, 3100, 100)

        trades = sim.process(order, price)

        # 체결 확인
        assert len(trades) == 1
        assert trades[0].trade_id == "limit-sell-1-fill-1"
        assert trades[0].pair.get_asset() == 5.0
        assert trades[0].pair.get_value() == 15000.0  # 5.0 * 3000

    def test_limit_order_not_filled(self):
        """체결 조건 불만족 시 빈 리스트."""
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="no-fill",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=40000.0,  # 시장 가격보다 훨씬 낮음
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        assert trades == []


class TestTradeSimulationSpotMarketOrders:
    """Spot Market 주문 처리 테스트."""

    def test_market_buy_order(self):
        """Market Buy 주문 전체 프로세스."""
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-buy-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=3.0,
            timestamp=1234567890,
            fee_rate=0.001,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        # 항상 체결
        assert len(trades) > 0

        # 총 수량 보존
        total_amount = sum(t.pair.get_asset() for t in trades)
        assert abs(total_amount - 3.0) < 1e-10

        # head 범위 체결 확인
        bodytop = price.bodytop()
        high = price.h
        for trade in trades:
            trade_price = trade.pair.get_value() / trade.pair.get_asset()
            assert bodytop <= trade_price <= high

    def test_market_sell_order(self):
        """Market Sell 주문 전체 프로세스."""
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-sell-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=2.0,
            timestamp=1234567890,
            fee_rate=0.001,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        # 항상 체결
        assert len(trades) > 0

        # 총 수량 보존
        total_amount = sum(t.pair.get_asset() for t in trades)
        assert abs(total_amount - 2.0) < 1e-10

        # tail 범위 체결 확인
        bodybottom = price.bodybottom()
        low = price.l
        for trade in trades:
            trade_price = trade.pair.get_value() / trade.pair.get_asset()
            assert low <= trade_price <= bodybottom


class TestTradeSimulationMultipleFills:
    """다중 체결 테스트."""

    def test_market_order_multiple_fills(self):
        """Market 주문의 다중 체결."""
        random.seed(10)  # 다중 체결이 발생하는 시드
        np.random.seed(10)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="multi-fill",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=0.5
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        if len(trades) > 1:
            # 각 Trade ID가 고유한지 확인
            trade_ids = [t.trade_id for t in trades]
            assert len(trade_ids) == len(set(trade_ids))

            # fill_index가 순차적인지 확인
            expected_ids = [f"multi-fill-fill-{i}" for i in range(1, len(trades) + 1)]
            assert trade_ids == expected_ids


class TestTradeSimulationTradeProperties:
    """Trade 속성 검증 테스트."""

    def test_trade_references_order(self):
        """Trade가 원본 Order를 참조."""
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="ref-test",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        for trade in trades:
            assert trade.order is order
            assert trade.order.order_id == "ref-test"

    def test_trade_timestamp_from_price(self):
        """Trade timestamp가 price.t에서 가져와짐."""
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="time-test",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1111111111  # order timestamp와 다름
        )

        price_timestamp = 9999999999
        price = Price("binance", "BTC/USDT", price_timestamp, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        for trade in trades:
            assert trade.timestamp == price_timestamp


class TestTradeSimulationUnknownOrderType:
    """알 수 없는 Order 타입 처리 테스트."""

    def test_raises_on_unknown_order_type(self):
        """알 수 없는 Order 타입은 ValueError 발생."""
        sim = TradeSimulation()

        # SpotOrder가 아닌 다른 타입
        class UnknownOrder:
            pass

        unknown_order = UnknownOrder()
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        with pytest.raises(ValueError, match="Unknown order type"):
            sim.process(unknown_order, price)


class TestTradeSimulationIntegration:
    """통합 테스트."""

    def test_end_to_end_limit_buy(self):
        """Limit Buy 전체 프로세스 통합 테스트."""
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="e2e-limit-buy",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1234567890,
            fee_rate=0.001
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        trades = sim.process(order, price)

        # 검증: 1개 체결
        assert len(trades) == 1

        trade = trades[0]
        # Trade ID
        assert trade.trade_id == "e2e-limit-buy-fill-1"
        # Asset
        assert trade.pair.get_asset_token().symbol == "BTC"
        assert trade.pair.get_asset() == 2.0
        # Value
        assert trade.pair.get_value_token().symbol == "USDT"
        assert trade.pair.get_value() == 100000.0
        # Fee
        assert trade.fee.symbol == "USDT"
        assert trade.fee.amount == 100.0
        # Timestamp
        assert trade.timestamp == price.t
        # Order 참조
        assert trade.order is order

    def test_end_to_end_market_sell(self):
        """Market Sell 전체 프로세스 통합 테스트."""
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "usdt", "1h")
        order = SpotOrder(
            order_id="e2e-market-sell",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1234567890,
            fee_rate=0.002,
            min_trade_amount=1.0
        )

        price = Price("binance", "ETH/USDT", 1234567890, 3100, 2900, 3050, 2950, 100)

        trades = sim.process(order, price)

        # 검증: 1~3개 체결
        assert 1 <= len(trades) <= 3

        # 총 수량 보존
        total_asset = sum(t.pair.get_asset() for t in trades)
        assert abs(total_asset - 10.0) < 1e-10

        # 각 Trade 검증
        for idx, trade in enumerate(trades, 1):
            # Trade ID
            assert trade.trade_id == f"e2e-market-sell-fill-{idx}"
            # Asset symbol
            assert trade.pair.get_asset_token().symbol == "ETH"
            # Value symbol
            assert trade.pair.get_value_token().symbol == "USDT"
            # Timestamp
            assert trade.timestamp == price.t
            # Order 참조
            assert trade.order is order

        # tail 범위 체결 확인
        bodybottom = price.bodybottom()
        low = price.l
        for trade in trades:
            trade_price = trade.pair.get_value() / trade.pair.get_asset()
            assert low <= trade_price <= bodybottom
