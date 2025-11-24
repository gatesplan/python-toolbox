"""Tests for Portfolio"""

import pytest
from financial_simulation.exchange.Core.Portfolio.Portfolio import Portfolio
from financial_assets.trade import SpotTrade
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType


class TestPortfolio:
    """Portfolio 테스트"""

    def test_deposit_currency(self):
        """화폐 입금 테스트"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)

        assert portfolio.get_balance("USDT") == 10000.0

    def test_withdraw_currency(self):
        """화폐 출금 테스트"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.withdraw_currency("USDT", 3000.0)

        assert portfolio.get_balance("USDT") == 7000.0

    def test_withdraw_insufficient_balance_raises_error(self):
        """사용 가능 잔고 부족 시 에러"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)

        with pytest.raises(ValueError, match="Insufficient"):
            portfolio.withdraw_currency("USDT", 15000.0)

    def test_get_balance_total(self):
        """총 잔고 조회 (예약 자산 포함)"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 5000.0)

        assert portfolio.get_balance("USDT") == 10000.0

    def test_get_available_balance(self):
        """사용 가능 잔고 조회 (총 잔고 - 예약)"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 5000.0)

        assert portfolio.get_available_balance("USDT") == 5000.0

    def test_get_locked_balance(self):
        """예약 자산 수량 조회"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 5000.0)
        portfolio.lock_currency("order_2", "USDT", 2000.0)

        assert portfolio.get_locked_balance("USDT") == 7000.0

    def test_lock_currency_success(self):
        """자산 예약 성공"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 5000.0)

        assert portfolio.get_available_balance("USDT") == 5000.0
        assert portfolio.get_locked_balance("USDT") == 5000.0

    def test_lock_currency_insufficient_raises_error(self):
        """사용 가능 잔고 부족 시 예약 실패"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)

        with pytest.raises(ValueError, match="Insufficient available balance"):
            portfolio.lock_currency("order_1", "USDT", 15000.0)

    def test_lock_currency_considers_existing_locks(self):
        """기존 예약을 고려한 예약"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 6000.0)

        # 남은 사용 가능 잔고: 4000
        with pytest.raises(ValueError, match="Insufficient available balance"):
            portfolio.lock_currency("order_2", "USDT", 5000.0)

        # 4000 이하는 성공
        portfolio.lock_currency("order_3", "USDT", 3000.0)
        assert portfolio.get_available_balance("USDT") == 1000.0

    def test_unlock_currency(self):
        """자산 예약 해제"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 5000.0)

        portfolio.unlock_currency("order_1")

        assert portfolio.get_available_balance("USDT") == 10000.0
        assert portfolio.get_locked_balance("USDT") == 0.0

    def test_process_buy_trade(self):
        """매수 거래 처리"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)

        # BTC 매수 주문 및 거래
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=0.1,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.1), Token("USDT", 5000.0))
        trade = SpotTrade(
            trade_id="trade_1",
            order=order,
            pair=pair,
            timestamp=1000,
            fee=Token("USDT", 10.0)
        )

        portfolio.process_trade(trade)

        # USDT 차감 (5000 + 10 수수료)
        assert portfolio.get_balance("USDT") == 4990.0
        # BTC 보유량 확인은 get_positions로
        positions = portfolio.get_positions()
        assert positions.get("BTC-USDT") == 0.1

    def test_process_sell_trade(self):
        """매도 거래 처리"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)

        # 먼저 BTC 매수
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        buy_order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=0.1,
            timestamp=1000
        )
        buy_pair = Pair(Token("BTC", 0.1), Token("USDT", 5000.0))
        buy_trade = SpotTrade(
            trade_id="trade_1",
            order=buy_order,
            pair=buy_pair,
            timestamp=1000,
            fee=None
        )
        portfolio.process_trade(buy_trade)

        # BTC 매도
        sell_order = SpotOrder(
            order_id="order_2",
            stock_address=stock_address,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            price=55000.0,
            amount=0.1,
            timestamp=2000
        )
        sell_pair = Pair(Token("BTC", 0.1), Token("USDT", 5500.0))
        sell_trade = SpotTrade(
            trade_id="trade_2",
            order=sell_order,
            pair=sell_pair,
            timestamp=2000,
            fee=Token("USDT", 10.0)
        )
        portfolio.process_trade(sell_trade)

        # USDT: 10000 - 5000 (매수) + 5500 (매도) - 10 (수수료) = 10490
        assert portfolio.get_balance("USDT") == 10490.0
        # BTC 포지션 청산
        positions = portfolio.get_positions()
        assert "BTC-USDT" not in positions

    def test_get_positions(self):
        """포지션 조회"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 20000.0)

        # BTC 매수
        btc_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        btc_order = SpotOrder(
            order_id="order_1",
            stock_address=btc_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=20000.0,
            amount=0.5,
            timestamp=1000
        )
        btc_pair = Pair(Token("BTC", 0.5), Token("USDT", 10000.0))
        btc_trade = SpotTrade("trade_1", btc_order, btc_pair, 1000, None)
        portfolio.process_trade(btc_trade)

        # ETH 매수
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_order = SpotOrder(
            order_id="order_2",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=2500.0,
            amount=2.0,
            timestamp=2000
        )
        eth_pair = Pair(Token("ETH", 2.0), Token("USDT", 5000.0))
        eth_trade = SpotTrade("trade_2", eth_order, eth_pair, 2000, None)
        portfolio.process_trade(eth_trade)

        positions = portfolio.get_positions()
        assert positions["BTC-USDT"] == 0.5
        assert positions["ETH-USDT"] == 2.0

    def test_get_currencies(self):
        """보유 화폐 목록 조회"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.deposit_currency("BTC", 0.5)

        currencies = portfolio.get_currencies()
        assert "USDT" in currencies
        assert "BTC" in currencies

    def test_get_wallet(self):
        """내부 SpotWallet 접근"""
        portfolio = Portfolio()
        wallet = portfolio.get_wallet()

        assert wallet is not None
        # SpotWallet이어야 함
        from financial_assets.wallet import SpotWallet
        assert isinstance(wallet, SpotWallet)

    def test_withdraw_considers_locked_balance(self):
        """출금 시 예약 자산 고려"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 10000.0)
        portfolio.lock_currency("order_1", "USDT", 6000.0)

        # 사용 가능: 4000
        portfolio.withdraw_currency("USDT", 3000.0)
        assert portfolio.get_balance("USDT") == 7000.0

        # 남은 사용 가능: 1000
        with pytest.raises(ValueError, match="Insufficient"):
            portfolio.withdraw_currency("USDT", 2000.0)

    def test_lock_position_success(self):
        """Position 잠금 성공"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 60000.0)

        # BTC 포지션 생성
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_buy",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=1.0,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 1.0), Token("USDT", 50000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        # Position 잠금
        portfolio.lock_position("order_sell", "BTC-USDT", 0.5)

        # 총 포지션은 그대로
        assert portfolio.get_positions()["BTC-USDT"] == 1.0
        # 사용 가능은 감소
        assert portfolio.get_available_position("BTC-USDT") == 0.5
        # 잠긴 수량 확인
        assert portfolio.get_locked_position("BTC-USDT") == 0.5

    def test_lock_position_insufficient_raises_error(self):
        """Position 잠금 실패 - 포지션 부족"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 60000.0)

        # BTC 포지션 생성 (1.0 BTC)
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_buy",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=1.0,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 1.0), Token("USDT", 50000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        # 2.0 BTC 잠금 시도 (보유: 1.0)
        with pytest.raises(ValueError, match="포지션 부족"):
            portfolio.lock_position("order_sell", "BTC-USDT", 2.0)

    def test_lock_position_considers_existing_locks(self):
        """Position 잠금 시 기존 잠금 고려"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 60000.0)

        # BTC 포지션 생성 (1.0 BTC)
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_buy",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=1.0,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 1.0), Token("USDT", 50000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        # 첫 번째 잠금 (0.6 BTC)
        portfolio.lock_position("order_1", "BTC-USDT", 0.6)
        assert portfolio.get_available_position("BTC-USDT") == 0.4

        # 두 번째 잠금 (0.3 BTC) - 성공
        portfolio.lock_position("order_2", "BTC-USDT", 0.3)
        assert portfolio.get_available_position("BTC-USDT") == pytest.approx(0.1)

        # 세 번째 잠금 (0.2 BTC) - 실패 (사용 가능: 0.1)
        with pytest.raises(ValueError, match="포지션 부족"):
            portfolio.lock_position("order_3", "BTC-USDT", 0.2)

    def test_unlock_position(self):
        """Position 잠금 해제"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 60000.0)

        # BTC 포지션 생성
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_buy",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=1.0,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 1.0), Token("USDT", 50000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        # Position 잠금
        portfolio.lock_position("order_sell", "BTC-USDT", 0.5)
        assert portfolio.get_available_position("BTC-USDT") == 0.5

        # 잠금 해제
        portfolio.unlock_currency("order_sell")
        assert portfolio.get_available_position("BTC-USDT") == 1.0
        assert portfolio.get_locked_position("BTC-USDT") == 0.0

    def test_get_available_position_no_position(self):
        """포지션이 없을 때 get_available_position"""
        portfolio = Portfolio()
        assert portfolio.get_available_position("BTC-USDT") == 0.0

    def test_get_locked_position_no_locks(self):
        """잠금이 없을 때 get_locked_position"""
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 60000.0)

        # BTC 포지션 생성
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_buy",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=1.0,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 1.0), Token("USDT", 50000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        # 잠금 없음
        assert portfolio.get_locked_position("BTC-USDT") == 0.0
