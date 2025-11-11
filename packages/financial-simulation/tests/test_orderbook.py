"""Tests for OrderBook"""

import pytest
from financial_simulation.exchange.Core.OrderBook.OrderBook import OrderBook
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import Side, OrderType, TimeInForce


class TestOrderBook:
    """OrderBook 테스트"""

    def test_add_order(self):
        """주문 추가"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000
        )

        order_book.add_order(order)

        assert order_book.get_order_count() == 1
        assert order_book.get_order("order_1") is not None

    def test_add_duplicate_order_raises_error(self):
        """중복 order_id 추가 시 에러"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000
        )

        order_book.add_order(order)

        with pytest.raises(ValueError, match="already exists"):
            order_book.add_order(order)

    def test_remove_order(self):
        """주문 제거"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000
        )

        order_book.add_order(order)
        order_book.remove_order("order_1")

        assert order_book.get_order_count() == 0
        assert order_book.get_order("order_1") is None

    def test_remove_nonexistent_order_raises_error(self):
        """존재하지 않는 주문 제거 시 에러"""
        order_book = OrderBook()

        with pytest.raises(KeyError, match="not found"):
            order_book.remove_order("order_999")

    def test_get_order(self):
        """특정 주문 조회"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000
        )

        order_book.add_order(order)
        retrieved_order = order_book.get_order("order_1")

        assert retrieved_order is not None
        assert retrieved_order.order_id == "order_1"

    def test_get_order_nonexistent(self):
        """존재하지 않는 주문 조회 시 None"""
        order_book = OrderBook()

        assert order_book.get_order("order_999") is None

    def test_get_orders_by_symbol(self):
        """심볼별 주문 조회"""
        order_book = OrderBook()

        # BTC/USDT 주문 2개
        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order1 = SpotOrder("order_1", btc_address, Side.BUY, OrderType.LIMIT, 50000.0, 0.1, 1000)
        order2 = SpotOrder("order_2", btc_address, Side.SELL, OrderType.LIMIT, 51000.0, 0.2, 2000)
        order_book.add_order(order1)
        order_book.add_order(order2)

        # ETH/USDT 주문 1개
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        order3 = SpotOrder("order_3", eth_address, Side.BUY, OrderType.LIMIT, 3000.0, 1.0, 3000)
        order_book.add_order(order3)

        btc_orders = order_book.get_orders_by_symbol("BTC/USDT")
        eth_orders = order_book.get_orders_by_symbol("ETH/USDT")

        assert len(btc_orders) == 2
        assert len(eth_orders) == 1
        assert all(o.order_id in ["order_1", "order_2"] for o in btc_orders)

    def test_get_orders_by_symbol_empty(self):
        """해당 심볼의 주문이 없을 때 빈 리스트"""
        order_book = OrderBook()

        orders = order_book.get_orders_by_symbol("BTC/USDT")
        assert orders == []

    def test_get_all_orders(self):
        """모든 주문 조회"""
        order_book = OrderBook()

        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order1 = SpotOrder("order_1", btc_address, Side.BUY, OrderType.LIMIT, 50000.0, 0.1, 1000)
        order2 = SpotOrder("order_2", btc_address, Side.SELL, OrderType.LIMIT, 51000.0, 0.2, 2000)
        order_book.add_order(order1)
        order_book.add_order(order2)

        all_orders = order_book.get_all_orders()
        assert len(all_orders) == 2

    def test_get_order_count(self):
        """주문 개수 조회"""
        order_book = OrderBook()

        assert order_book.get_order_count() == 0

        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order1 = SpotOrder("order_1", btc_address, Side.BUY, OrderType.LIMIT, 50000.0, 0.1, 1000)
        order_book.add_order(order1)

        assert order_book.get_order_count() == 1

    def test_expire_orders_gtd(self):
        """GTD (Good Till Date) 만료 처리"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

        # 만료 시간이 2000인 주문
        order1 = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000,
            time_in_force=TimeInForce.GTD,
            expire_timestamp=2000
        )

        # 만료 시간이 3000인 주문
        order2 = SpotOrder(
            order_id="order_2",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.2,
            timestamp=1000,
            time_in_force=TimeInForce.GTD,
            expire_timestamp=3000
        )

        order_book.add_order(order1)
        order_book.add_order(order2)

        # 현재 시간 2500: order_1 만료, order_2 유효
        expired_ids = order_book.expire_orders(2500)

        assert len(expired_ids) == 1
        assert "order_1" in expired_ids
        assert order_book.get_order_count() == 1
        assert order_book.get_order("order_1") is None
        assert order_book.get_order("order_2") is not None

    def test_expire_orders_no_expiry(self):
        """만료 시간 없는 주문은 만료되지 않음"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

        # GTC (Good Till Cancel) - 만료 시간 없음
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000
            # time_in_force, expire_timestamp 없음
        )

        order_book.add_order(order)
        expired_ids = order_book.expire_orders(99999)

        assert len(expired_ids) == 0
        assert order_book.get_order_count() == 1

    def test_remove_order_updates_symbol_index(self):
        """주문 제거 시 symbol_index 업데이트"""
        order_book = OrderBook()
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")

        order1 = SpotOrder("order_1", stock_address, Side.BUY, OrderType.LIMIT, 50000.0, 0.1, 1000)
        order2 = SpotOrder("order_2", stock_address, Side.BUY, OrderType.LIMIT, 51000.0, 0.2, 2000)
        order_book.add_order(order1)
        order_book.add_order(order2)

        order_book.remove_order("order_1")

        btc_orders = order_book.get_orders_by_symbol("BTC/USDT")
        assert len(btc_orders) == 1
        assert btc_orders[0].order_id == "order_2"
