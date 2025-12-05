"""SpotExchange Symbol API 테스트

Symbol 객체와 str의 상호 호환성 테스트
"""

import pytest
import pandas as pd
import uuid
from financial_simulation.exchange.API.SpotExchange import SpotExchange
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.candle import Candle
from financial_assets.multicandle import MultiCandle
from financial_assets.stock_address import StockAddress
from financial_assets.symbol import Symbol
from financial_assets.constants import OrderSide, OrderType, TimeInForce
from financial_assets.order import SpotOrder


class TestSpotExchangeSymbolAPI:
    """Symbol 객체 지원 테스트"""

    @pytest.fixture
    def market_data(self):
        """테스트용 MarketData 생성"""
        btc_addr = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_df = pd.DataFrame({
            'timestamp': [1000 + i * 60 for i in range(100)],
            'open': [50000.0] * 100,
            'high': [51000.0] * 100,
            'low': [49000.0] * 100,
            'close': [50000.0] * 100,
            'volume': [100.0] * 100
        })
        btc_candle = Candle(btc_addr, btc_df)
        mc = MultiCandle([btc_candle])
        return MarketData(mc, start_offset=10)

    @pytest.fixture
    def exchange(self, market_data):
        """테스트용 SpotExchange 생성"""
        return SpotExchange(
            initial_balance=100000.0,
            market_data=market_data,
            maker_fee_ratio=0.001,
            taker_fee_ratio=0.002,
            quote_currency="USDT"
        )

    @pytest.fixture
    def btc_symbol(self):
        """BTC/USDT Symbol 객체"""
        return Symbol("BTC/USDT")

    # ========== 시장 조회 메서드 테스트 ==========

    def test_get_current_price_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 현재가 조회"""
        price_with_symbol = exchange.get_current_price(btc_symbol)
        price_with_str = exchange.get_current_price("BTC/USDT")

        assert price_with_symbol == price_with_str
        assert price_with_symbol == 50000.0

    def test_get_orderbook_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 호가창 조회"""
        orderbook_with_symbol = exchange.get_orderbook(btc_symbol)
        orderbook_with_str = exchange.get_orderbook("BTC/USDT")

        assert len(orderbook_with_symbol.asks) == len(orderbook_with_str.asks)
        assert len(orderbook_with_symbol.bids) == len(orderbook_with_str.bids)

    def test_get_candles_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 캔들 조회"""
        candles_with_symbol = exchange.get_candles(btc_symbol, limit=10)
        candles_with_str = exchange.get_candles("BTC/USDT", limit=10)

        assert len(candles_with_symbol) == len(candles_with_str)
        assert (candles_with_symbol == candles_with_str).all().all()

    # ========== 주문 조회 메서드 테스트 ==========

    def test_get_open_orders_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 미체결 주문 조회"""
        # LIMIT 주문 생성 (미체결)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=25000.0,  # 낮은 가격 = 미체결
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order)

        orders_with_symbol = exchange.get_open_orders(btc_symbol)
        orders_with_str = exchange.get_open_orders("BTC/USDT")

        assert len(orders_with_symbol) == len(orders_with_str)
        assert len(orders_with_symbol) == 1

    def test_get_trade_history_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 거래 내역 조회"""
        # MARKET 주문 실행
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.05,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order)

        trades_with_symbol = exchange.get_trade_history(btc_symbol)
        trades_with_str = exchange.get_trade_history("BTC/USDT")

        assert len(trades_with_symbol) == len(trades_with_str)
        assert len(trades_with_symbol) > 0

    # ========== 포지션 조회 메서드 테스트 ==========

    def test_get_position_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 포지션 조회"""
        # MARKET 주문으로 포지션 생성
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        trades = exchange.place_order(order)
        total_filled = sum(trade.pair.get_asset() for trade in trades)

        position_with_symbol = exchange.get_position(btc_symbol)
        position_with_str = exchange.get_position("BTC/USDT")

        assert position_with_symbol == position_with_str
        assert position_with_symbol == total_filled

    def test_get_available_position_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 사용 가능 포지션 조회"""
        # MARKET 주문으로 포지션 생성
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order)

        available_with_symbol = exchange.get_available_position(btc_symbol)
        available_with_str = exchange.get_available_position("BTC/USDT")

        assert available_with_symbol == available_with_str
        assert available_with_symbol > 0

    def test_get_locked_position_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 잠긴 포지션 조회"""
        # 초기 상태 (잠금 없음)
        locked_with_symbol = exchange.get_locked_position(btc_symbol)
        locked_with_str = exchange.get_locked_position("BTC/USDT")

        assert locked_with_symbol == locked_with_str
        assert locked_with_symbol == 0.0

    def test_get_position_value_with_symbol(self, exchange, btc_symbol):
        """Symbol 객체로 포지션 가치 조회"""
        # MARKET 주문으로 포지션 생성
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=None,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01
        )
        exchange.place_order(order)

        value_with_symbol = exchange.get_position_value(btc_symbol)
        value_with_str = exchange.get_position_value("BTC/USDT")

        assert value_with_symbol == value_with_str
        assert "book_value" in value_with_symbol
        assert "market_value" in value_with_symbol
        assert "pnl" in value_with_symbol
        assert "pnl_ratio" in value_with_symbol

    # ========== Currency 메서드 테스트 ==========

    def test_get_currencies(self, exchange):
        """보유 화폐 목록 조회"""
        currencies = exchange.get_currencies()

        assert "USDT" in currencies
        assert len(currencies) >= 1

    def test_get_locked_balance(self, exchange):
        """잠긴 잔고 조회"""
        # 초기 상태 (잠금 없음)
        locked = exchange.get_locked_balance("USDT")

        assert locked == 0.0

        # LIMIT 주문 생성 (잔고 잠금)
        order = SpotOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=25000.0,
            amount=0.1,
            timestamp=exchange.get_current_timestamp(),
            min_trade_amount=0.01,
            time_in_force=TimeInForce.GTC
        )
        exchange.place_order(order)

        # 잠금 확인
        locked_after = exchange.get_locked_balance("USDT")
        assert locked_after > 0

    # ========== Dash 형식 호환성 테스트 ==========

    def test_symbol_with_dash_format(self, exchange):
        """Dash 형식("BTC-USDT") Symbol도 지원"""
        symbol_dash = Symbol("BTC-USDT")

        # Symbol("BTC-USDT")과 Symbol("BTC/USDT")은 동일
        assert symbol_dash == Symbol("BTC/USDT")

        # API 호출 가능
        price = exchange.get_current_price(symbol_dash)
        assert price == 50000.0

    # ========== 에러 처리 테스트 ==========

    def test_invalid_symbol_str(self, exchange):
        """잘못된 심볼 문자열"""
        with pytest.raises(KeyError):
            exchange.get_current_price("INVALID/USDT")

    def test_invalid_symbol_object(self, exchange):
        """잘못된 Symbol 객체"""
        invalid_symbol = Symbol("INVALID/USDT")

        with pytest.raises(KeyError):
            exchange.get_current_price(invalid_symbol)
