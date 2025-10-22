"""Tests for SpotLimitBuyWorker"""

import pytest
from financial_simulation.tradesim import SpotLimitBuyWorker, CalculationTool
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotSide
from financial_assets.price import Price
from financial_assets.stock_address import StockAddress


class TestSpotLimitBuyWorker:
    """SpotLimitBuyWorker 테스트"""

    def test_fill_when_price_below_order(self):
        """시장 가격이 주문 가격 이하일 때 체결"""
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

        # 시장 가격이 주문 가격 이하
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        calc_tool = CalculationTool()
        worker = SpotLimitBuyWorker()
        trades = worker(calc_tool, order, price)

        assert len(trades) == 1
        assert trades[0].side == SpotSide.BUY
        assert trades[0].pair.get_asset() == 1.0

    def test_no_fill_when_price_above_order(self):
        """시장 가격이 주문 가격보다 높을 때 미체결"""
        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usd", "1d")
        order = SpotOrder(
            order_id="order-2",
            stock_address=stock_address,
            side=SpotSide.BUY,
            order_type="limit",
            price=50000.0,
            amount=1.0,
            timestamp=1234567890
        )

        # 시장 가격이 주문 가격보다 높음
        price = Price("binance", "BTC/USD", 1234567890, 52000, 50500, 51500, 51000, 100)

        calc_tool = CalculationTool()
        worker = SpotLimitBuyWorker()
        trades = worker(calc_tool, order, price)

        assert len(trades) == 0
