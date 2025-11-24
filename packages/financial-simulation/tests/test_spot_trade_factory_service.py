import pytest
import sys
from pathlib import Path

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.Service import SpotTradeFactoryService
from financial_simulation.tradesim.InternalStruct import TradeParams
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType


class TestSpotTradeFactoryService:

    def test_create_trades_single(self):
        # 단일 Trade 생성
        service = SpotTradeFactoryService()

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
        assert trades[0].trade_id == "test-1-fill-1"
        assert trades[0].pair.get_asset() == 1.0
        assert trades[0].pair.get_value() == 50000.0

    def test_create_trades_multiple(self):
        # 복수 Trade 생성
        service = SpotTradeFactoryService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-2",
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
        assert trades[0].trade_id == "test-2-fill-1"
        assert trades[1].trade_id == "test-2-fill-2"
        assert trades[2].trade_id == "test-2-fill-3"

    def test_create_trades_fee_calculation(self):
        # 수수료 계산
        service = SpotTradeFactoryService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-3",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
            fee_rate=0.001,  # 0.1%
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=1)
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert trades[0].fee is not None
        assert trades[0].fee.symbol == "USDT"
        assert trades[0].fee.amount == 50.0  # 50000 * 0.001

    def test_create_trades_trade_id_format(self):
        # ID 형식 검증
        service = SpotTradeFactoryService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-12345",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
        )

        params_list = [
            TradeParams(fill_amount=1.0, fill_price=50000.0, fill_index=5)
        ]

        trades = service.create_trades(order, params_list, 1000000)

        assert trades[0].trade_id == "order-12345-fill-5"

    def test_create_trades_pair_construction(self):
        # Pair 구성 검증
        service = SpotTradeFactoryService()

        stock_address = StockAddress("crypto", "binance", "spot", "eth", "btc", "1d")
        order = SpotOrder(
            order_id="test-5",
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

        assert trades[0].pair.get_asset_token().symbol == "ETH"
        assert trades[0].pair.get_asset() == 10.0
        assert trades[0].pair.get_value_token().symbol == "BTC"
        assert trades[0].pair.get_value() == 0.5  # 10 * 0.05
