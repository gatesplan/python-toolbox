"""Tests for SpotExecutionDirector."""

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

from financial_simulation.tradesim.spot_execution.spot_execution_director import SpotExecutionDirector
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import Side, OrderType


class TestSpotExecutionDirectorInitialization:
    """SpotExecutionDirector 초기화 테스트."""

    def test_director_initialization(self):
        """Director 초기화."""
        director = SpotExecutionDirector()
        assert director is not None
        assert hasattr(director, "_limit_worker")
        assert hasattr(director, "_market_buy_worker")
        assert hasattr(director, "_market_sell_worker")


class TestSpotExecutionDirectorRouting:
    """Worker 라우팅 테스트."""

    def test_route_to_limit_worker(self):
        """Limit 주문은 LimitWorker로 라우팅."""
        random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-limit",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        # body 범위에 있어 체결됨
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        # LimitWorker 결과 확인
        assert isinstance(params_list, list)

    def test_route_to_market_buy_worker(self):
        """Market Buy 주문은 MarketBuyWorker로 라우팅."""
        random.seed(42)
        np.random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-market-buy",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        # MarketBuyWorker는 항상 체결
        assert len(params_list) > 0

        # head 범위에서 체결되어야 함
        bodytop = price.bodytop()
        high = price.h
        for params in params_list:
            assert bodytop <= params.fill_price <= high

    def test_route_to_market_sell_worker(self):
        """Market Sell 주문은 MarketSellWorker로 라우팅."""
        random.seed(42)
        np.random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-market-sell",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        # MarketSellWorker는 항상 체결
        assert len(params_list) > 0

        # tail 범위에서 체결되어야 함
        bodybottom = price.bodybottom()
        low = price.l
        for params in params_list:
            assert low <= params.fill_price <= bodybottom


class TestSpotExecutionDirectorValidation:
    """파라미터 검증 테스트."""

    def test_invalid_price_type(self):
        """잘못된 Price 타입."""
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="order-invalid",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        invalid_price = "not a price object"

        with pytest.raises(ValueError, match="Invalid parameters"):
            director.execute(order, invalid_price)

    def test_missing_order_attributes(self):
        """Order 속성 누락."""
        director = SpotExecutionDirector()

        # order_type 속성이 없는 mock 객체
        class InvalidOrder:
            pass

        invalid_order = InvalidOrder()
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        with pytest.raises(ValueError, match="Invalid parameters"):
            director.execute(invalid_order, price)


class TestSpotExecutionDirectorLimitOrders:
    """Limit 주문 처리 테스트."""

    def test_limit_buy_filled(self):
        """Limit Buy 체결."""
        random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-buy",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1234567890
        )

        # body 범위에 주문 가격 포함
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        assert len(params_list) == 1
        assert params_list[0].fill_amount == 2.0
        assert params_list[0].fill_price == 50000.0

    def test_limit_sell_filled(self):
        """Limit Sell 체결."""
        random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-sell",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=3.0,
            timestamp=1234567890
        )

        # body 범위에 주문 가격 포함
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 49500, 50500, 100)

        params_list = director.execute(order, price)

        assert len(params_list) == 1
        assert params_list[0].fill_amount == 3.0
        assert params_list[0].fill_price == 50000.0


class TestSpotExecutionDirectorMarketOrders:
    """Market 주문 처리 테스트."""

    def test_market_buy_always_fills(self):
        """Market Buy는 항상 체결."""
        random.seed(42)
        np.random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-buy",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=5.0,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        # 항상 체결
        assert len(params_list) > 0

        # 총 수량 보존
        total_amount = sum(p.fill_amount for p in params_list)
        assert abs(total_amount - 5.0) < 1e-10

    def test_market_sell_always_fills(self):
        """Market Sell은 항상 체결."""
        random.seed(42)
        np.random.seed(42)
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-sell",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=7.0,
            timestamp=1234567890,
            min_trade_amount=0.1
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        # 항상 체결
        assert len(params_list) > 0

        # 총 수량 보존
        total_amount = sum(p.fill_amount for p in params_list)
        assert abs(total_amount - 7.0) < 1e-10


class TestSpotExecutionDirectorEdgeCases:
    """엣지 케이스 테스트."""

    def test_unknown_order_type(self):
        """알 수 없는 order_type."""
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="unknown",
            stock_address=stock_address,
            side=Side.BUY,
            order_type="unknown_type",  # 잘못된 타입
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        with pytest.raises(ValueError, match="Unknown order_type or side"):
            director.execute(order, price)

    def test_empty_result_from_limit_worker(self):
        """LimitWorker가 빈 리스트 반환."""
        director = SpotExecutionDirector()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="no-fill",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=40000.0,  # 체결 조건 불만족
            amount=1.0,
            timestamp=1234567890
        )

        # 시장 가격이 주문 가격보다 높음
        price = Price("binance", "BTC/USDT", 1234567890, 51000, 49000, 50500, 49500, 100)

        params_list = director.execute(order, price)

        assert params_list == []
