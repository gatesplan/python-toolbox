"""Tests for TradeSimulation"""

import pytest
from financial_simulation.tradesim import TradeSimulation
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotSide
from financial_assets.price import Price
from financial_assets.stock_address import StockAddress


class TestTradeSimulation:
    """TradeSimulation 통합 테스트"""

    def test_initialization(self):
        """TradeSimulation 초기화 테스트"""
        sim = TradeSimulation()

        assert sim._limit_buy_worker is not None
        assert sim._limit_sell_worker is not None
        assert sim._market_buy_worker is not None
        assert sim._market_sell_worker is not None

    def test_route_limit_buy(self):
        """Limit Buy 주문 라우팅 테스트"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        sim = TradeSimulation()
        trades = sim.process(order, price)

        assert isinstance(trades, list)

    def test_route_limit_sell(self):
        """Limit Sell 주문 라우팅 테스트"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=SpotSide.SELL,
            order_type="limit",
            price=51000.0,
            amount=1.0,
            timestamp=1234567890
        )

        price = Price("binance", "BTC/USD", 1234567890, 52000, 51000, 51500, 51500, 100)

        sim = TradeSimulation()
        trades = sim.process(order, price)

        assert isinstance(trades, list)

    def test_validate_invalid_price(self):
        """잘못된 Price 타입 검증 테스트"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-1",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        invalid_price = "not a price object"

        sim = TradeSimulation()
        is_valid = sim._validate_process_param(order, invalid_price)

        assert is_valid == False
