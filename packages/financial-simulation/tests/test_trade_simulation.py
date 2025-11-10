import pytest
import random
import sys
from pathlib import Path
import numpy as np

package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

financial_assets_root = package_root.parent / "financial-assets"
sys.path.insert(0, str(financial_assets_root))

from financial_simulation.tradesim import TradeSimulation
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.price import Price
from financial_assets.constants import Side, OrderType


class TestTradeSimulationInitialization:

    def test_service_initialization(self):
        # Service 초기화
        sim = TradeSimulation()
        assert sim is not None
        assert hasattr(sim, "_limit_fill_service")
        assert hasattr(sim, "_market_buy_fill_service")
        assert hasattr(sim, "_market_sell_fill_service")
        assert hasattr(sim, "_trade_factory_service")


class TestTradeSimulationSpotLimitOrders:

    def test_limit_buy_order(self):
        # 지정가 매수 body 범위에서 체결
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-buy-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=105.0,  # body 범위 (100~110)
            amount=1.5,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        # body 범위이므로 반드시 체결
        assert len(trades) == 1
        assert trades[0].order == order
        assert trades[0].timestamp == price.t
        assert trades[0].pair.get_asset() == 1.5

    def test_limit_sell_order(self):
        # 지정가 매도 body 범위에서 체결
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-sell-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=105.0,  # body 범위 (100~110)
            amount=1.5,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        # body 범위이므로 반드시 체결
        assert len(trades) == 1
        assert trades[0].pair.get_asset() == 1.5

    def test_limit_order_body_zone(self):
        # body 범위에서 전량 체결
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-body-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=105.0,
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        assert len(trades) == 1
        assert trades[0].pair.get_asset() == 1.0

    def test_limit_order_wick_zone(self):
        # wick 범위에서 확률적 체결
        random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-wick-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=115.0,  # head 범위
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        # 여러 번 실행
        results = []
        for _ in range(100):
            trades = sim.process(order, price)
            results.append(len(trades))

        # 확률적 체결 검증 (0개 또는 1개 이상)
        assert min(results) == 0  # 실패 케이스 존재
        assert max(results) >= 1  # 성공 케이스 존재


class TestTradeSimulationSpotMarketOrders:

    def test_market_buy_order(self):
        # 시장가 매수
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-buy-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.5,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        assert len(trades) > 0  # 항상 체결
        for trade in trades:
            assert trade.order == order

    def test_market_sell_order(self):
        # 시장가 매도
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-sell-1",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.5,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        assert len(trades) > 0  # 항상 체결

    def test_market_order_slippage(self):
        # 슬리피지 검증
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")

        # 매수는 head 범위 (110~120)
        buy_order = SpotOrder(
            order_id="market-buy-2",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        buy_trades = sim.process(buy_order, price)
        for trade in buy_trades:
            # head 범위 내
            fill_price = trade.pair.get_value() / trade.pair.get_asset()
            assert 110.0 <= fill_price <= 120.0

        # 매도는 tail 범위 (90~100)
        sell_order = SpotOrder(
            order_id="market-sell-2",
            stock_address=stock_address,
            side=Side.SELL,
            order_type=OrderType.MARKET,
            price=None,
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        sell_trades = sim.process(sell_order, price)
        for trade in sell_trades:
            # tail 범위 내
            fill_price = trade.pair.get_value() / trade.pair.get_asset()
            assert 90.0 <= fill_price <= 100.0

    def test_market_order_split(self):
        # 분할 체결
        random.seed(42)
        np.random.seed(42)
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="market-split-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=10.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        # 1~3개로 분할
        assert 1 <= len(trades) <= 3

        # 총합 검증
        total_amount = sum(trade.pair.get_asset() for trade in trades)
        assert abs(total_amount - 10.0) < 0.0001


class TestTradeSimulationErrorHandling:

    def test_unknown_order_type(self):
        # 미지원 주문 타입
        sim = TradeSimulation()

        class UnknownOrder:
            pass

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        with pytest.raises(ValueError):
            sim.process(UnknownOrder(), price)

    def test_limit_order_outside_range(self):
        # 캔들 범위 밖 가격은 체결되지 않음
        sim = TradeSimulation()

        stock_address = StockAddress("crypto", "binance", "spot", "btc", "usdt", "1d")
        order = SpotOrder(
            order_id="limit-outside-1",
            stock_address=stock_address,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=130.0,  # 범위 밖 (h=120)
            amount=1.0,
            timestamp=1000000,
            min_trade_amount=0.01,
        )

        price = Price("binance", "BTCUSDT", 1000000, 120.0, 90.0, 100.0, 110.0, 1000.0)

        trades = sim.process(order, price)

        # 범위 밖이므로 체결 없음
        assert len(trades) == 0
