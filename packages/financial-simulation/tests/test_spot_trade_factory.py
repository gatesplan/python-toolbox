"""Tests for SpotTradeFactory."""

import pytest
import sys
from pathlib import Path

# 패키지 루트를 sys.path에 추가 (설치 없이 테스트)
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

# financial-assets 패키지도 sys.path에 추가
financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.trade_factory.spot_trade_factory import SpotTradeFactory
from financial_simulation.tradesim.trade_params import TradeParams
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import Side


class TestSpotTradeFactoryCreation:
    """SpotTradeFactory 생성 및 기본 동작 테스트."""

    def test_factory_initialization(self):
        """팩토리 초기화."""
        factory = SpotTradeFactory()
        assert factory is not None

    def test_create_buy_trade(self):
        """매수 거래 생성."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-123",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.001
        )

        params = TradeParams(
            fill_amount=1.0,
            fill_price=50000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        assert trade is not None
        assert trade.trade_id == "order-123-fill-1"
        assert trade.order == order
        assert trade.timestamp == 1234567890
        assert trade.pair.get_asset_token().symbol == "BTC"
        assert trade.pair.get_asset() == 1.0
        assert trade.pair.get_value_token().symbol == "USDT"
        assert trade.pair.get_value() == 50000.0

    def test_create_sell_trade(self):
        """매도 거래 생성."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "usdt", "1h")
        order = SpotOrder(
            order_id="order-456",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=10.0,
            timestamp=1234567890,
            fee_rate=0.001
        )

        params = TradeParams(
            fill_amount=10.0,
            fill_price=3000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        assert trade is not None
        assert trade.trade_id == "order-456-fill-1"
        assert trade.pair.get_asset_token().symbol == "ETH"
        assert trade.pair.get_asset() == 10.0
        assert trade.pair.get_value_token().symbol == "USDT"
        assert trade.pair.get_value() == 30000.0


class TestSpotTradeFactoryFeeCalculation:
    """수수료 계산 테스트."""

    def test_fee_calculation_with_fee_rate(self):
        """수수료율이 있는 경우 수수료 계산."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-fee-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.001  # 0.1%
        )

        params = TradeParams(
            fill_amount=1.0,
            fill_price=50000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        # 거래 금액: 50000.0
        # 수수료: 50000.0 * 0.001 = 50.0
        assert trade.fee is not None
        assert trade.fee.symbol == "USDT"
        assert trade.fee.amount == 50.0

    def test_no_fee_when_fee_rate_is_zero(self):
        """수수료율이 0인 경우 수수료 없음."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-no-fee",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890,
            fee_rate=0.0
        )

        params = TradeParams(
            fill_amount=1.0,
            fill_price=50000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        assert trade.fee is None


class TestSpotTradeFactoryTradeId:
    """Trade ID 생성 테스트."""

    def test_trade_id_format(self):
        """Trade ID 형식: {order_id}-fill-{fill_index}."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="my-order-123",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=3.0,
            timestamp=1234567890
        )

        params1 = TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)
        params2 = TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=2)
        params3 = TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=3)

        trade1 = factory.create_spot_trade(order, params1, 1234567890)
        trade2 = factory.create_spot_trade(order, params2, 1234567890)
        trade3 = factory.create_spot_trade(order, params3, 1234567890)

        assert trade1.trade_id == "my-order-123-fill-1"
        assert trade2.trade_id == "my-order-123-fill-2"
        assert trade3.trade_id == "my-order-123-fill-3"


class TestSpotTradeFactoryPairConstruction:
    """Pair 구성 테스트."""

    def test_pair_asset_token(self):
        """Asset Token 구성 확인."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=2.5,
            timestamp=1234567890
        )

        params = TradeParams(
            fill_amount=2.5,
            fill_price=50000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        assert trade.pair.get_asset_token().symbol == "BTC"
        assert trade.pair.get_asset() == 2.5

    def test_pair_value_token(self):
        """Value Token 구성 확인."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "usdt", "1h")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=5.0,
            timestamp=1234567890
        )

        params = TradeParams(
            fill_amount=5.0,
            fill_price=3000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        # Value = fill_price * fill_amount = 3000.0 * 5.0 = 15000.0
        assert trade.pair.get_value_token().symbol == "USDT"
        assert trade.pair.get_value() == 15000.0

    def test_partial_fill(self):
        """부분 체결 처리."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-partial",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=10.0,  # 총 10.0
            timestamp=1234567890
        )

        # 부분 체결: 3.0만 체결
        params = TradeParams(
            fill_amount=3.0,
            fill_price=50000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        assert trade.pair.get_asset() == 3.0
        assert trade.pair.get_value() == 150000.0  # 3.0 * 50000.0


class TestSpotTradeFactoryOrderReference:
    """Order 객체 연결 테스트."""

    def test_trade_references_order(self):
        """생성된 Trade가 원본 Order를 참조."""
        factory = SpotTradeFactory()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-ref",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        params = TradeParams(
            fill_amount=1.0,
            fill_price=50000.0,
            fill_index=1
        )

        trade = factory.create_spot_trade(order, params, 1234567890)

        assert trade.order is order
        assert trade.order.order_id == "order-ref"
