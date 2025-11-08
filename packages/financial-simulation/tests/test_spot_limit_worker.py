"""Tests for SpotLimitWorker."""

import pytest
import random
import sys
from pathlib import Path

# 패키지 루트를 sys.path에 추가 (설치 없이 테스트)
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

# financial-assets 패키지도 sys.path에 추가
financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim.spot_execution.spot_limit_worker import SpotLimitWorker
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import Side


class TestSpotLimitWorkerBuyOrders:
    """매수 지정가 주문 테스트."""

    def test_buy_order_not_filled_when_price_too_high(self):
        """주문 가격이 캔들 low보다 낮으면 체결 안 됨."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=48000.0,  # low보다 낮은 가격
            amount=1.0,
            timestamp=1234567890
        )

        # low=49000 > order.price=48000 → none 범위 → 체결 안 됨
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 50500, 100)

        params_list = worker(order, price)

        assert len(params_list) == 0

    def test_buy_order_filled_in_body(self):
        """Body 범위에서 100% 전량 체결."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.5,
            timestamp=1234567890
        )

        # 주문 가격 50000이 body 범위에 있음
        # o=51000, c=49000 → bodybottom=49000, bodytop=51000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 51000, 49000, 100)

        params_list = worker(order, price)

        assert len(params_list) == 1
        assert params_list[0].fill_amount == 1.5
        assert params_list[0].fill_price == 50000.0
        assert params_list[0].fill_index == 1

    def test_buy_order_probabilistic_fill_in_tail(self):
        """Tail 범위에서 확률적 체결."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-3",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=48500.0,  # tail 범위
            amount=2.0,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        # 주문 가격 48500이 tail 범위에 있음
        # o=51000, c=49000, l=48000 → bodybottom=49000, tail: 48000~49000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 51000, 49000, 100)

        # 여러 번 실행해서 확률적 동작 확인 (각 반복마다 다른 seed)
        results = []
        for seed in range(10):
            random.seed(seed)
            params_list = worker(order, price)
            results.append(len(params_list))

        # 적어도 한 번은 체결이 발생해야 함 (확률적이므로)
        # tail 범위에서 30% 실패, 30% 전량, 40% 부분 체결 → 10번 중 최소 1번은 체결
        assert sum(results) > 0, "10번 시도 중 한 번도 체결되지 않음"


class TestSpotLimitWorkerSellOrders:
    """매도 지정가 주문 테스트."""

    def test_sell_order_not_filled_when_price_too_low(self):
        """주문 가격이 캔들 high보다 높으면 체결 안 됨."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-sell-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="limit",
            price=52000.0,  # high보다 높은 가격
            amount=1.0,
            timestamp=1234567890
        )

        # high=51000 < order.price=52000 → none 범위 → 체결 안 됨
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 50500, 100)

        params_list = worker(order, price)

        assert len(params_list) == 0

    def test_sell_order_filled_in_body(self):
        """Body 범위에서 100% 전량 체결."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-sell-2",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="limit",
            price=50000.0,
            amount=2.5,
            timestamp=1234567890
        )

        # 주문 가격 50000이 body 범위에 있음
        # o=49000, c=51000 → bodybottom=49000, bodytop=51000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 49000, 51000, 100)

        params_list = worker(order, price)

        assert len(params_list) == 1
        assert params_list[0].fill_amount == 2.5
        assert params_list[0].fill_price == 50000.0
        assert params_list[0].fill_index == 1

    def test_sell_order_probabilistic_fill_in_head(self):
        """Head 범위에서 확률적 체결."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-sell-3",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="limit",
            price=51500.0,  # head 범위
            amount=3.0,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        # 주문 가격 51500이 head 범위에 있음
        # o=49000, c=51000, h=52000 → bodytop=51000, head: 51000~52000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 49000, 51000, 100)

        # 여러 번 실행해서 확률적 동작 확인 (각 반복마다 다른 seed)
        results = []
        for seed in range(10):
            random.seed(seed)
            params_list = worker(order, price)
            results.append(len(params_list))

        # 적어도 한 번은 체결이 발생해야 함
        # head 범위에서 30% 실패, 30% 전량, 40% 부분 체결 → 10번 중 최소 1번은 체결
        assert sum(results) > 0, "10번 시도 중 한 번도 체결되지 않음"


class TestSpotLimitWorkerPartialFills:
    """부분 체결 테스트."""

    def test_partial_fill_generates_multiple_params(self):
        """부분 체결 시 여러 TradeParams 생성."""
        random.seed(10)  # 부분 체결이 발생하는 시드
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-partial",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=48500.0,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=0.5
        )

        # tail 범위에서 확률적 체결
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 51000, 49000, 100)

        # 여러 번 실행해서 부분 체결 발생 확인
        for _ in range(20):
            params_list = worker(order, price)
            if len(params_list) > 1:
                # 부분 체결 발생
                # 수량 합이 전체 수량과 같아야 함
                total_amount = sum(p.fill_amount for p in params_list)
                assert abs(total_amount - 10.0) < 1e-10

                # 인덱스가 순차적이어야 함
                indices = [p.fill_index for p in params_list]
                assert indices == list(range(1, len(params_list) + 1))
                break


class TestSpotLimitWorkerEdgeCases:
    """엣지 케이스 테스트."""

    def test_order_price_at_boundary(self):
        """주문 가격이 경계에 있을 때."""
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-boundary",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=49000.0,  # bodybottom과 동일
            amount=1.0,
            timestamp=1234567890
        )

        # o=51000, c=49000 → bodybottom=49000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 51000, 49000, 100)

        params_list = worker(order, price)

        # body 범위에 포함되므로 전량 체결
        assert len(params_list) == 1
        assert params_list[0].fill_amount == 1.0

    def test_min_trade_amount_none(self):
        """min_trade_amount가 None일 때 기본값 사용."""
        random.seed(10)
        worker = SpotLimitWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-no-min",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="limit",
            price=48500.0,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=None  # None
        )

        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 51000, 49000, 100)

        # 에러 없이 실행되어야 함
        params_list = worker(order, price)
        assert isinstance(params_list, list)
