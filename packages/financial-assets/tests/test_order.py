"""
Tests for Order class
"""
import pytest
from financial_assets.token import Token
from financial_assets.pair import Pair, PairStack
from financial_assets.order import Order, OrderInfo, OrderStatus
from financial_assets.stock_address import StockAddress


class TestOrderInit:
    """Order 초기화 테스트"""

    def test_order_creation(self):
        """Order 객체 생성"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-123",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.5,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.5), Token("USD", 75000.0))])

        order = Order(info=info, assets=assets)

        assert order.info == info
        assert order.assets == assets
        assert order.order_id == "order-123"
        assert order.price == 50000.0
        assert order.quantity == 1.5
        assert order.filled_quantity == 0.0
        assert order.status == OrderStatus.OPEN


class TestOrderDelegation:
    """Order 속성 위임 테스트"""

    def test_order_info_property_delegation(self):
        """OrderInfo 속성들이 Order에서 직접 접근 가능"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-456",
            side="sell",
            order_type="limit",
            price=51000.0,
            quantity=2.0,
            filled_quantity=0.5,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.5), Token("USD", 76500.0))])

        order = Order(info=info, assets=assets)

        # 위임된 속성 검증
        assert order.order_id == "order-456"
        assert order.price == 51000.0
        assert order.quantity == 2.0
        assert order.filled_quantity == 0.5
        assert order.status == OrderStatus.PARTIALLY_FILLED


class TestOrderFillByValueAmount:
    """Order fill_by_value_amount 테스트"""

    def test_fill_by_value_amount_partial(self):
        """value 기준 부분 체결"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-789",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        # 1.0 BTC = 50000 USD
        assets = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        order = Order(info=info, assets=assets)

        # 15000 USD만큼 체결 (30%)
        filled = order.fill_by_value_amount(15000.0)

        # 체결된 자산
        assert abs(filled.total_value_amount() - 15000.0) < 0.01
        assert abs(filled.total_asset_amount() - 0.3) < 0.0001

        # 남은 자산
        assert abs(order.assets.total_value_amount() - 35000.0) < 0.01
        assert abs(order.assets.total_asset_amount() - 0.7) < 0.0001

    def test_fill_by_value_amount_full(self):
        """value 기준 전량 체결"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-abc",
            side="sell",
            order_type="limit",
            price=52000.0,
            quantity=0.5,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 0.5), Token("USD", 26000.0))])
        order = Order(info=info, assets=assets)

        # 전량 체결
        filled = order.fill_by_value_amount(26000.0)

        # 체결된 자산
        assert filled.total_value_amount() == 26000.0
        assert filled.total_asset_amount() == 0.5

        # 남은 자산 없음
        assert order.assets.is_empty()

    def test_fill_by_value_amount_multiple_layers(self):
        """여러 레이어 걸쳐 value 기준 체결"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-multi",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=2.3,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.8), Token("USD", 42000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 27000.0)),
        ])
        order = Order(info=info, assets=assets)

        # 60000 USD만큼 체결
        filled = order.fill_by_value_amount(60000.0)

        # 체결된 자산
        assert abs(filled.total_value_amount() - 60000.0) < 0.01

        # 남은 자산
        assert abs(order.assets.total_value_amount() - 59000.0) < 0.01

    def test_fill_by_value_amount_exceeds_raises(self):
        """총 value 초과 체결 시 에러"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-err",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        order = Order(info=info, assets=assets)

        with pytest.raises(ValueError, match="exceeds total"):
            order.fill_by_value_amount(100000.0)


class TestOrderFillByAssetAmount:
    """Order fill_by_asset_amount 테스트"""

    def test_fill_by_asset_amount_partial(self):
        """asset 기준 부분 체결"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-asset",
            side="sell",
            order_type="limit",
            price=51000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.0), Token("USD", 51000.0))])
        order = Order(info=info, assets=assets)

        # 0.4 BTC 체결
        filled = order.fill_by_asset_amount(0.4)

        # 체결된 자산
        assert abs(filled.total_asset_amount() - 0.4) < 0.0001
        assert abs(filled.total_value_amount() - 20400.0) < 0.01

        # 남은 자산
        assert abs(order.assets.total_asset_amount() - 0.6) < 0.0001
        assert abs(order.assets.total_value_amount() - 30600.0) < 0.01

    def test_fill_by_asset_amount_full(self):
        """asset 기준 전량 체결"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-full",
            side="buy",
            order_type="limit",
            price=49000.0,
            quantity=2.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 2.0), Token("USD", 98000.0))])
        order = Order(info=info, assets=assets)

        # 전량 체결
        filled = order.fill_by_asset_amount(2.0)

        assert filled.total_asset_amount() == 2.0
        assert order.assets.is_empty()

    def test_fill_by_asset_amount_multiple_layers(self):
        """여러 레이어 걸쳐 asset 기준 체결"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-layers",
            side="sell",
            order_type="limit",
            price=50000.0,
            quantity=1.8,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.8), Token("USD", 42000.0)),
        ])
        order = Order(info=info, assets=assets)

        # 1.5 BTC 체결 (비율 기반)
        filled = order.fill_by_asset_amount(1.5)

        # 체결된 자산
        assert abs(filled.total_asset_amount() - 1.5) < 0.01

        # 남은 자산
        assert abs(order.assets.total_asset_amount() - 0.3) < 0.01

    def test_fill_by_asset_amount_exceeds_raises(self):
        """총 asset 초과 체결 시 에러"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-exceed",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        order = Order(info=info, assets=assets)

        with pytest.raises(ValueError, match="exceeds total"):
            order.fill_by_asset_amount(2.0)


class TestOrderEquality:
    """Order 동등성 비교 테스트"""

    def test_orders_with_same_ticker_are_equal(self):
        """같은 ticker의 Order는 같음"""
        info1 = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-1",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets1 = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])

        info2 = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-2",  # 다른 ID
            side="sell",
            order_type="limit",
            price=51000.0,  # 다른 가격
            quantity=2.0,  # 다른 수량
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567891,  # 다른 시간
        )
        assets2 = PairStack([Pair(Token("BTC", 2.0), Token("USD", 102000.0))])

        order1 = Order(info=info1, assets=assets1)
        order2 = Order(info=info2, assets=assets2)

        # PairStack의 ticker가 같으면 같음
        assert order1 == order2

    def test_orders_with_different_ticker_are_not_equal(self):
        """다른 ticker의 Order는 다름"""
        info1 = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-btc",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets1 = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])

        info2 = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-eth",
            side="buy",
            order_type="limit",
            price=3000.0,
            quantity=10.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets2 = PairStack([Pair(Token("ETH", 10.0), Token("USD", 30000.0))])

        order1 = Order(info=info1, assets=assets1)
        order2 = Order(info=info2, assets=assets2)

        assert order1 != order2

    def test_order_equality_with_non_order_object(self):
        """Order가 아닌 객체와 비교 시 False"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-test",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        order = Order(info=info, assets=assets)

        assert order != "not an order"
        assert order != 123
        assert order != None


class TestOrderStringRepresentations:
    """Order 문자열 표현 테스트"""

    def test_order_repr(self):
        """Order __repr__ 테스트"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-repr",
            side="buy",
            order_type="limit",
            price=50000.0,
            quantity=1.0,
            filled_quantity=0.0,
            status=OrderStatus.OPEN,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        order = Order(info=info, assets=assets)

        repr_str = repr(order)
        assert "Order" in repr_str
        assert "info=" in repr_str
        assert "assets=" in repr_str

    def test_order_str(self):
        """Order __str__ 테스트"""
        info = OrderInfo(
            stock_address=StockAddress(
                archetype="crypto",
                exchange="binance",
                tradetype="spot",
                base="btc",
                quote="usd",
                timeframe="1d"
            ),
            order_id="order-str",
            side="sell",
            order_type="limit",
            price=51000.0,
            quantity=2.0,
            filled_quantity=0.5,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=1234567890,
        )
        assets = PairStack([Pair(Token("BTC", 1.5), Token("USD", 76500.0))])
        order = Order(info=info, assets=assets)

        str_str = str(order)
        assert "Order" in str_str
        assert "order-str" in str_str
        assert "51000" in str_str
        assert "2.0" in str_str
        assert "0.5" in str_str
        assert "PARTIALLY_FILLED" in str_str
