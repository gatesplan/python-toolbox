import pytest
import random
import sys
from pathlib import Path
import numpy as np

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.Service import SpotMarketSellFillService
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import Side, OrderType


class TestSpotMarketSellFillService:

    def test_execute_always_fills(self):
        # 항상 체결
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        assert len(params_list) > 0

    def test_execute_slippage_range(self):
        # tail 범위에서 가격 샘플링 (90~100)
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-2",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # 모든 가격이 tail 범위 (90~100) 내
        for params in params_list:
            assert 90.0 <= params.fill_price <= 100.0

    def test_execute_split_count(self):
        # 1~3개 분할
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-3",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        # 여러 번 실행
        for _ in range(10):
            params_list = service.execute(order, price)
            assert 1 <= len(params_list) <= 3

    def test_execute_price_sampling(self):
        # 각 조각마다 다른 가격으로 샘플링
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-4",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        # 여러 번 실행하여 분할 발생 시 가격 차이 확인
        found_different_prices = False
        for _ in range(100):
            params_list = service.execute(order, price)
            if len(params_list) >= 2:
                prices = [p.fill_price for p in params_list]
                # 각 조각이 서로 다른 가격을 가져야 함
                if len(set(prices)) > 1:
                    found_different_prices = True
                    break

        assert found_different_prices, "분할 체결 시 각 조각은 다른 가격을 가져야 함"
