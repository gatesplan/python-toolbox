"""Tests for SpotMarketSellWorker."""

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

from financial_simulation.tradesim.spot_execution.spot_market_sell_worker import SpotMarketSellWorker
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import Side


class TestSpotMarketSellWorkerBasic:
    """SpotMarketSellWorker 기본 동작 테스트."""

    def test_always_fills(self):
        """시장가 매도는 항상 체결됨."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = worker(order, price)

        # 항상 체결되므로 결과가 비어있지 않음
        assert len(params_list) > 0

    def test_returns_1_to_3_fills(self):
        """1~3개의 체결 생성."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        # 여러 번 실행해서 1~3개 범위 확인
        results = []
        for seed in range(20):
            random.seed(seed)
            np.random.seed(seed)
            params_list = worker(order, price)
            results.append(len(params_list))

        # 1~3개 범위 내
        assert all(1 <= count <= 3 for count in results)


class TestSpotMarketSellWorkerSlippage:
    """슬리피지 테스트."""

    def test_fill_price_in_tail_range(self):
        """체결 가격이 tail 범위(low ~ bodybottom) 내에 있음."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-slippage",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=5.0,
            timestamp=1234567890
        )

        # o=50500, c=49500 → bodybottom=49500, l=49000
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        bodybottom = price.bodybottom()
        low = price.l

        params_list = worker(order, price)

        # 모든 체결 가격이 tail 범위 내
        for params in params_list:
            assert low <= params.fill_price <= bodybottom

    def test_slippage_below_close(self):
        """슬리피지로 인해 close보다 낮은 가격에 체결."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-slip",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=3.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = worker(order, price)

        # close=49500, 모든 체결 가격은 bodybottom(49500) 이하
        for params in params_list:
            assert params.fill_price <= price.bodybottom()


class TestSpotMarketSellWorkerAmountSplit:
    """수량 분할 테스트."""

    def test_total_amount_preserved(self):
        """분할 후 총 수량이 보존됨."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        total_amount = 10.0
        order = SpotOrder(
            order_id="order-amount",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=total_amount,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = worker(order, price)

        # 총 수량 합이 원래 수량과 동일
        total_filled = sum(p.fill_amount for p in params_list)
        assert abs(total_filled - total_amount) < 1e-10

    def test_fill_indices_sequential(self):
        """fill_index가 1부터 순차적."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-index",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=5.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = worker(order, price)

        indices = [p.fill_index for p in params_list]
        assert indices == list(range(1, len(params_list) + 1))


class TestSpotMarketSellWorkerDifferentPrices:
    """각 체결마다 다른 가격 테스트."""

    def test_multiple_fills_have_different_prices(self):
        """여러 체결의 가격이 다를 수 있음 (확률적)."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-prices",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        # 여러 번 실행해서 다른 가격 발생 확인
        for seed in range(50):
            random.seed(seed)
            np.random.seed(seed)
            params_list = worker(order, price)

            if len(params_list) > 1:
                prices = [p.fill_price for p in params_list]
                # 적어도 하나는 다른 가격이 나올 수 있음
                if len(set(prices)) > 1:
                    # 다른 가격이 발견됨 - 테스트 통과
                    return

        # 50번 시도했는데도 모든 체결이 동일한 가격이면 로직 오류
        pytest.fail("50회 시도 중 모든 다중 체결이 동일한 가격 - get_price_sample 로직 검증 필요")


class TestSpotMarketSellWorkerMinTradeAmount:
    """min_trade_amount 처리 테스트."""

    def test_with_min_trade_amount(self):
        """min_trade_amount가 지정된 경우."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-min",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=1.0
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = worker(order, price)

        # 총 수량 보존
        total_filled = sum(p.fill_amount for p in params_list)
        assert abs(total_filled - 10.0) < 1e-10

    def test_without_min_trade_amount(self):
        """min_trade_amount가 None인 경우 기본값 사용."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-no-min",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=10.0,
            timestamp=1234567890,
            min_trade_amount=None
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = worker(order, price)

        # 에러 없이 실행되고 총 수량 보존
        total_filled = sum(p.fill_amount for p in params_list)
        assert abs(total_filled - 10.0) < 1e-10


class TestSpotMarketSellWorkerWithDifferentCandles:
    """다양한 캔들 상황 테스트."""

    def test_with_bullish_candle(self):
        """양봉(close > open)에서 동작."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-bull",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=5.0,
            timestamp=1234567890
        )

        # 양봉: o=49000, c=51000 → bodybottom=49000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 49000, 51000, 100)

        params_list = worker(order, price)

        # tail 범위: 48000 ~ 49000
        for params in params_list:
            assert 48000 <= params.fill_price <= 49000

    def test_with_bearish_candle(self):
        """음봉(close < open)에서 동작."""
        random.seed(42)
        np.random.seed(42)
        worker = SpotMarketSellWorker()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-bear",
            stock_address=stock_address,
            side=Side.SELL,
            order_type="market",
            price=None,
            amount=5.0,
            timestamp=1234567890
        )

        # 음봉: o=51000, c=49000 → bodybottom=49000
        price = Price("binance", "BTC/USDT", 1234567890, 52000, 48000, 51000, 49000, 100)

        params_list = worker(order, price)

        # tail 범위: 48000 ~ 49000
        for params in params_list:
            assert 48000 <= params.fill_price <= 49000
