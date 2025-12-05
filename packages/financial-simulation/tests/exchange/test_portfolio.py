"""Portfolio Symbol 지원 단위 테스트"""

import pytest
from financial_simulation.exchange.Core.Portfolio.Portfolio import Portfolio
from financial_assets.symbol import Symbol
from financial_assets.trade import SpotTrade
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType
from financial_assets.pair import Pair
from financial_assets.token import Token


class TestPortfolioSymbolSupport:
    """Portfolio Symbol 객체 지원 테스트"""

    @pytest.fixture
    def portfolio(self):
        """테스트용 Portfolio 생성"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 1000000.0)  # 1M USDT (테스트용 충분한 금액)
        return portfolio

    def _create_buy_trade(self, order_id: str, btc_amount: float, price: float = 50000.0):
        """BUY 거래 생성 헬퍼"""
        usdt_value = btc_amount * price
        fee = usdt_value * 0.002

        return SpotTrade(
            trade_id=f"trade_{order_id}",
            order=SpotOrder(
                order_id=order_id,
                stock_address=StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                price=price,
                amount=btc_amount,
                timestamp=1000,
                min_trade_amount=0.001
            ),
            pair=Pair(
                asset=Token("BTC", btc_amount),
                value=Token("USDT", usdt_value)
            ),
            timestamp=1000,
            fee=Token("USDT", fee)
        )

    # ========== get_available_position 테스트 ==========

    def test_get_available_position_with_str(self, portfolio):
        """str ticker로 사용 가능 포지션 조회"""
        # 초기 상태 (포지션 없음)
        available = portfolio.get_available_position("BTC-USDT")
        assert available == 0.0

    def test_get_available_position_with_symbol_slash(self, portfolio):
        """Symbol(slash) 객체로 사용 가능 포지션 조회"""
        symbol = Symbol("BTC/USDT")
        available = portfolio.get_available_position(symbol)
        assert available == 0.0

    def test_get_available_position_with_symbol_dash(self, portfolio):
        """Symbol(dash) 객체로 사용 가능 포지션 조회"""
        symbol = Symbol("BTC-USDT")
        available = portfolio.get_available_position(symbol)
        assert available == 0.0

    def test_get_available_position_after_trade(self, portfolio):
        """거래 후 사용 가능 포지션 조회 (str vs Symbol 동일)"""
        # BUY 거래로 포지션 생성
        trade = self._create_buy_trade("order_1", 1.0)
        portfolio.process_trade(trade)

        # str vs Symbol 조회 결과 동일
        available_str = portfolio.get_available_position("BTC-USDT")
        available_symbol = portfolio.get_available_position(Symbol("BTC/USDT"))

        assert available_str == 1.0
        assert available_symbol == 1.0
        assert available_str == available_symbol

    # ========== get_locked_position 테스트 ==========

    def test_get_locked_position_with_str(self, portfolio):
        """str ticker로 잠긴 포지션 조회"""
        locked = portfolio.get_locked_position("BTC-USDT")
        assert locked == 0.0

    def test_get_locked_position_with_symbol(self, portfolio):
        """Symbol 객체로 잠긴 포지션 조회"""
        symbol = Symbol("BTC/USDT")
        locked = portfolio.get_locked_position(symbol)
        assert locked == 0.0

    def test_get_locked_position_after_lock(self, portfolio):
        """포지션 잠금 후 조회 (str vs Symbol 동일)"""
        # 먼저 포지션 생성
        trade = self._create_buy_trade("order_1", 2.0)
        portfolio.process_trade(trade)

        # 포지션 잠금
        portfolio.lock_position("promise_1", "BTC-USDT", 1.0)

        # str vs Symbol 조회 결과 동일
        locked_str = portfolio.get_locked_position("BTC-USDT")
        locked_symbol = portfolio.get_locked_position(Symbol("BTC/USDT"))

        assert locked_str == 1.0
        assert locked_symbol == 1.0
        assert locked_str == locked_symbol

    # ========== lock_position 테스트 ==========

    def test_lock_position_with_str(self, portfolio):
        """str ticker로 포지션 잠금"""
        # 포지션 생성
        trade = self._create_buy_trade("order_1", 1.0)
        portfolio.process_trade(trade)

        # str로 잠금
        portfolio.lock_position("promise_1", "BTC-USDT", 0.5)

        # 검증
        locked = portfolio.get_locked_position("BTC-USDT")
        available = portfolio.get_available_position("BTC-USDT")

        assert locked == 0.5
        assert available == 0.5

    def test_lock_position_with_symbol(self, portfolio):
        """Symbol 객체로 포지션 잠금"""
        # 포지션 생성
        trade = self._create_buy_trade("order_1", 1.0)
        portfolio.process_trade(trade)

        # Symbol 객체로 잠금
        symbol = Symbol("BTC/USDT")
        portfolio.lock_position("promise_2", symbol, 0.3)

        # 검증
        locked = portfolio.get_locked_position(symbol)
        available = portfolio.get_available_position(symbol)

        assert locked == 0.3
        assert available == 0.7

    def test_lock_position_insufficient_available(self, portfolio):
        """사용 가능 포지션 부족 시 ValueError"""
        # 포지션 생성
        trade = self._create_buy_trade("order_1", 1.0)
        portfolio.process_trade(trade)

        # 보유량보다 많이 잠그려고 시도
        symbol = Symbol("BTC/USDT")
        with pytest.raises(ValueError, match="포지션 부족"):
            portfolio.lock_position("promise_fail", symbol, 2.0)

    # ========== Symbol dash 변환 테스트 ==========

    def test_symbol_slash_to_dash_conversion(self, portfolio):
        """Symbol("BTC/USDT") → "BTC-USDT" 변환 검증"""
        # 포지션 생성
        trade = self._create_buy_trade("order_1", 1.0)
        portfolio.process_trade(trade)

        # slash Symbol로 잠금
        symbol_slash = Symbol("BTC/USDT")
        portfolio.lock_position("promise_1", symbol_slash, 0.5)

        # dash str로 조회 가능
        locked_dash = portfolio.get_locked_position("BTC-USDT")
        assert locked_dash == 0.5

    def test_symbol_dash_format_direct(self, portfolio):
        """Symbol("BTC-USDT") 직접 사용"""
        # 포지션 생성
        trade = self._create_buy_trade("order_1", 1.0)
        portfolio.process_trade(trade)

        # dash Symbol로 잠금
        symbol_dash = Symbol("BTC-USDT")
        portfolio.lock_position("promise_2", symbol_dash, 0.3)

        # 조회 가능
        locked = portfolio.get_locked_position(symbol_dash)
        assert locked == 0.3

    # ========== 복합 시나리오 테스트 ==========

    def test_mixed_str_and_symbol_usage(self, portfolio):
        """str과 Symbol 혼용 사용"""
        # 포지션 생성
        trade = self._create_buy_trade("order_1", 10.0)
        portfolio.process_trade(trade)

        # str로 잠금
        portfolio.lock_position("promise_1", "BTC-USDT", 3.0)

        # Symbol로 잠금
        portfolio.lock_position("promise_2", Symbol("BTC/USDT"), 2.0)

        # 총 잠금량 확인 (str과 Symbol 모두 사용)
        locked_str = portfolio.get_locked_position("BTC-USDT")
        locked_symbol = portfolio.get_locked_position(Symbol("BTC/USDT"))

        assert locked_str == 5.0
        assert locked_symbol == 5.0

        # 사용 가능 수량
        available = portfolio.get_available_position(Symbol("BTC/USDT"))
        assert available == 5.0
