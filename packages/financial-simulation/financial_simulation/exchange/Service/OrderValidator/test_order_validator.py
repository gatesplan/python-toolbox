"""OrderValidator 테스트."""

import pytest
from financial_assets.order import SpotOrder
from financial_assets.constants import OrderSide, OrderType
from financial_assets.price import Price
from financial_assets.stock_address import StockAddress
from financial_simulation.exchange.Core.Portfolio import Portfolio
from financial_simulation.exchange.Core.MarketData import MarketData
from .OrderValidator import OrderValidator


@pytest.fixture
def portfolio():
    """테스트용 Portfolio 생성."""
    portfolio = Portfolio()
    portfolio.deposit_currency("USDT", 10000.0)
    portfolio.deposit_currency("BTC", 1.0)
    return portfolio


@pytest.fixture
def market_data():
    """테스트용 MarketData 생성."""
    data = {
        "BTC/USDT": [
            Price(exchange="test", market="BTC/USDT", t=1000, o=50000, h=51000, l=49000, c=50000, v=100),
            Price(exchange="test", market="BTC/USDT", t=2000, o=50000, h=52000, l=49000, c=51000, v=150),
        ]
    }
    return MarketData(data)


@pytest.fixture
def validator(portfolio, market_data):
    """테스트용 OrderValidator 생성."""
    return OrderValidator(portfolio, market_data)


@pytest.fixture
def stock_address():
    """테스트용 StockAddress 생성."""
    return StockAddress(
        archetype="spot",
        exchange="test",
        tradetype="spot",
        base="BTC",
        quote="USDT",
        timeframe="1m"
    )


class TestOrderValidatorBuyOrders:
    """BUY 주문 검증 테스트."""

    def test_buy_limit_sufficient_balance(self, validator, stock_address):
        """BUY LIMIT 주문 - 잔고 충분."""
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.1,
            timestamp=1000,
        )
        # 필요 자금: 50000 * 0.1 = 5000 (사용 가능: 10000)
        validator.validate_order(order)  # 예외 발생하지 않아야 함

    def test_buy_limit_insufficient_balance(self, validator, stock_address):
        """BUY LIMIT 주문 - 잔고 부족."""
        order = SpotOrder(
            order_id="order_2",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=1.0,
            timestamp=1000,
        )
        # 필요 자금: 50000 * 1.0 = 50000 (사용 가능: 10000)
        with pytest.raises(ValueError, match="잔고 부족"):
            validator.validate_order(order)

    def test_buy_market_sufficient_balance(self, validator, stock_address):
        """BUY MARKET 주문 - 현재가 기준 잔고 충분."""
        order = SpotOrder(
            order_id="order_3",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=1000,
        )
        # 현재가: 50000, 필요 자금: 50000 * 0.1 = 5000 (사용 가능: 10000)
        validator.validate_order(order)  # 예외 발생하지 않아야 함

    def test_buy_market_insufficient_balance(self, validator, stock_address):
        """BUY MARKET 주문 - 현재가 기준 잔고 부족."""
        order = SpotOrder(
            order_id="order_4",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000,
        )
        # 현재가: 50000, 필요 자금: 50000 * 1.0 = 50000 (사용 가능: 10000)
        with pytest.raises(ValueError, match="잔고 부족"):
            validator.validate_order(order)


class TestOrderValidatorSellOrders:
    """SELL 주문 검증 테스트."""

    def test_sell_limit_sufficient_asset(self, validator, stock_address):
        """SELL LIMIT 주문 - 자산 충분."""
        order = SpotOrder(
            order_id="order_5",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=1000,
        )
        # 필요 자산: 0.5 BTC (보유: 1.0 BTC)
        validator.validate_order(order)  # 예외 발생하지 않아야 함

    def test_sell_limit_insufficient_asset(self, validator, stock_address):
        """SELL LIMIT 주문 - 자산 부족."""
        order = SpotOrder(
            order_id="order_6",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=2.0,
            timestamp=1000,
        )
        # 필요 자산: 2.0 BTC (보유: 1.0 BTC)
        with pytest.raises(ValueError, match="자산 부족"):
            validator.validate_order(order)

    def test_sell_market_sufficient_asset(self, validator, stock_address):
        """SELL MARKET 주문 - 자산 충분."""
        order = SpotOrder(
            order_id="order_7",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.5,
            timestamp=1000,
        )
        # 필요 자산: 0.5 BTC (보유: 1.0 BTC)
        validator.validate_order(order)  # 예외 발생하지 않아야 함


class TestOrderValidatorLockedAssets:
    """잠긴 자산 고려 테스트."""

    def test_buy_with_locked_balance(self, validator, stock_address):
        """BUY 주문 - 미체결 주문으로 잠긴 잔고 고려."""
        # USDT 5000 잠금
        validator._portfolio.lock_currency("lock_1", "USDT", 5000.0)

        order = SpotOrder(
            order_id="order_8",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.15,
            timestamp=1000,
        )
        # 필요 자금: 50000 * 0.15 = 7500
        # 총 잔고: 10000, 잠긴 금액: 5000, 사용 가능: 5000
        with pytest.raises(ValueError, match="잔고 부족"):
            validator.validate_order(order)

    def test_sell_with_locked_asset(self, validator, stock_address):
        """SELL 주문 - 미체결 주문으로 잠긴 자산 고려."""
        # BTC 0.7 잠금
        validator._portfolio.lock_currency("lock_2", "BTC", 0.7)

        order = SpotOrder(
            order_id="order_9",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=50000.0,
            amount=0.5,
            timestamp=1000,
        )
        # 필요 자산: 0.5 BTC
        # 총 보유: 1.0 BTC, 잠긴 자산: 0.7 BTC, 사용 가능: 0.3 BTC
        with pytest.raises(ValueError, match="자산 부족"):
            validator.validate_order(order)
