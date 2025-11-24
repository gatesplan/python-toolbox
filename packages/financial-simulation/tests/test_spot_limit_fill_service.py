import pytest
import random
import sys
from pathlib import Path

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.Service import SpotLimitFillService
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import OrderSide, OrderType


class TestSpotLimitFillService:

    def test_execute_body_zone(self):
        # body 범위에서 전량 체결
        service = SpotLimitFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=105.0,  # body 범위 (100~110)
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        assert len(params_list) == 1
        assert params_list[0].fill_amount == 1.0
        assert params_list[0].fill_price == 105.0
        assert params_list[0].fill_index == 1

    def test_execute_wick_zone_probability(self):
        # wick 범위에서 확률적 체결
        service = SpotLimitFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-2",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=115.0,  # head 범위 (110~120)
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        # 여러 번 실행하여 확률 분포 확인
        results = []
        for _ in range(100):
            params_list = service.execute(order, price)
            results.append(len(params_list))

        # 30% 실패 (0개), 30% 전량 (1개), 40% 부분 (1~3개)
        fail_count = results.count(0)
        success_count = len(results) - fail_count

        # 실패가 있어야 함 (확률적)
        assert fail_count > 0
        # 성공도 있어야 함
        assert success_count > 0

    def test_execute_none_zone(self):
        # 범위 밖에서 체결 없음
        service = SpotLimitFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-3",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=130.0,  # 범위 밖 (h=120)
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        params_list = service.execute(order, price)

        assert len(params_list) == 0

    def test_execute_partial_fill(self):
        # 부분 체결 시 총합 검증
        random.seed(42)
        service = SpotLimitFillService()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="test-4",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=115.0,  # head 범위
            amount=10.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        # 부분 체결 발생 시
        for _ in range(100):
            params_list = service.execute(order, price)
            if len(params_list) > 1:
                total = sum(p.fill_amount for p in params_list)
                assert abs(total - 10.0) < 0.0001
                break
