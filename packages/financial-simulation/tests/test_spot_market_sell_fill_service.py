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
from financial_assets.constants import Side, OrderType, TimeInForce


class TestSpotMarketSellFillService:

    def test_execute_small_order_full_fill(self):
        # 소액 주문 (0.1% 이하): 전량 체결 보장
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-small-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,  # 0.1 / 500 = 0.0002 = 0.02% (0.1% 이하)
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # 전량 체결 확인
        total_amount = sum(p.fill_amount for p in params_list)
        assert abs(total_amount - 0.1) < 0.0001

    def test_execute_medium_order_high_fill_ratio(self):
        # 중간 주문 (0.1% ~ 1%): 95-100% 체결
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-medium-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=2.0,  # 2.0 / 500 = 0.004 = 0.4% (0.1% ~ 1%)
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # 95-100% 체결 확인
        total_amount = sum(p.fill_amount for p in params_list)
        fill_ratio = total_amount / 2.0
        assert 0.95 <= fill_ratio <= 1.0

    def test_execute_large_order_partial_fill(self):
        # 큰 주문 (1% ~ 5%): 60-90% 체결
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-large-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,  # 10.0 / 500 = 0.02 = 2% (1% ~ 5%)
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # 60-90% 체결 확인
        total_amount = sum(p.fill_amount for p in params_list)
        fill_ratio = total_amount / 10.0
        assert 0.6 <= fill_ratio <= 0.9

    def test_execute_huge_order_low_fill_ratio(self):
        # 거대 주문 (5% ~ 20%): 20-50% 체결
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-huge-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=40.0,  # 40.0 / 500 = 0.08 = 8% (5% ~ 20%)
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # 20-50% 체결 확인
        total_amount = sum(p.fill_amount for p in params_list)
        fill_ratio = total_amount / 40.0
        assert 0.2 <= fill_ratio <= 0.5

    def test_execute_excessive_order_minimal_fill(self):
        # 초대형 주문 (20% 초과): IOC 5-15% 체결
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-excessive-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=250.0,  # 250.0 / 500 = 0.5 = 50% (20% 초과)
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # 5-15% 체결 확인
        total_amount = sum(p.fill_amount for p in params_list)
        fill_ratio = total_amount / 250.0
        assert 0.05 <= fill_ratio <= 0.15

    def test_execute_excessive_order_fok_fails(self):
        # 초대형 주문 (20% 초과) + FOK: 무조건 실패
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-excessive-fok-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=250.0,  # 250.0 / 500 = 0.5 = 50% (20% 초과)
            timestamp=1000000,
            min_trade_amount=0.01,
            time_in_force=TimeInForce.FOK,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        # FOK 무조건 실패
        assert len(params_list) == 0

    def test_execute_slippage_range(self):
        # tail 범위에서 가격 샘플링 (90~100)
        random.seed(42)
        np.random.seed(42)
        service = SpotMarketSellFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-slippage-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,  # 소액 주문으로 전량 체결 보장
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
            order_id="test-split-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,  # 소액 주문으로 전량 체결 보장
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
            order_id="test-price-sampling-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,  # 소액 주문으로 전량 체결 보장
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
