"""PositionManager 테스트

PositionManager는 포지션 조회 및 통계를 제공하는 Service Layer 컴포넌트입니다.
Book Value(보유 가치)와 Market Value(현재 시장 가치)를 구분하여 계산하고,
이를 기반으로 손익 및 자산 배분 통계를 제공합니다.

핵심 개념:
- Book Value (보유 가치): 매수 당시 지불한 총 금액 (PairStack.total_value_amount())
- Market Value (현재 가치): 현재 시장 가격 × 보유 수량
- Unrealized PnL (미실현 손익): Market Value - Book Value
"""

import pytest
from financial_simulation.exchange.Service.PositionManager.PositionManager import PositionManager
from financial_simulation.exchange.Core.Portfolio.Portfolio import Portfolio
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.price import Price
from financial_assets.trade import SpotTrade
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType


class TestPositionManager:
    """PositionManager 기능 테스트 Suite

    테스트 대상:
    1. 포지션 조회
    2. 가치 계산 (Book Value, Market Value, Currency Value, Total Value)
    3. 손익 계산 (PnL, PnL Ratio)
    4. 자산 배분 통계 (Allocation)
    """

    @pytest.fixture
    def market_data(self):
        """시장 데이터 Fixture

        테스트용 시장 가격 데이터를 생성합니다.

        설정된 가격:
        - BTC/USDT: 50,000 USDT (종가 기준)
        - ETH/USDT: 2,500 USDT (종가 기준)

        Returns:
            MarketData: 초기화된 MarketData 인스턴스
        """
        data = {
            "BTC/USDT": [Price(o=49000, h=51000, l=48000, c=50000, v=100, t=1000, exchange="binance", market="spot")],
            "ETH/USDT": [Price(o=2400, h=2600, l=2300, c=2500, v=200, t=1000, exchange="binance", market="spot")],
        }
        market_data = MarketData(data, availability_threshold=0.0, offset=0)
        market_data.reset()
        return market_data

    @pytest.fixture
    def portfolio(self):
        """포트폴리오 Fixture

        테스트용 포트폴리오를 생성합니다.

        초기 자금:
        - USDT: 100,000

        Returns:
            Portfolio: 초기화된 Portfolio 인스턴스
        """
        portfolio = Portfolio()
        portfolio.deposit_currency("USDT", 100000.0)
        return portfolio

    # ===== 초기화 및 기본 기능 테스트 =====

    def test_init(self, portfolio, market_data):
        """PositionManager 초기화 테스트

        Given: Portfolio와 MarketData가 준비됨
        When: PositionManager를 초기화
        Then: 정상적으로 인스턴스가 생성됨
        """
        position_manager = PositionManager(portfolio, market_data, initial_balance=10000.0)

        assert position_manager is not None

    def test_get_positions(self, portfolio, market_data):
        """포지션 목록 조회 테스트

        Given: BTC 0.5개를 매수한 포트폴리오
        When: get_positions() 호출
        Then: {"BTC-USDT": 0.5} 형식으로 포지션 반환

        검증 내용:
        - Portfolio.get_positions()를 래핑하여 동일한 결과 반환
        - ticker 형식: "BTC-USDT" (하이픈 구분)
        - 보유 수량: 0.5 BTC
        """
        # Given: BTC 포지션 생성
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 25000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        # When: PositionManager로 포지션 조회
        position_manager = PositionManager(portfolio, market_data, initial_balance=10000.0)
        positions = position_manager.get_positions()

        # Then: BTC-USDT 포지션이 0.5 BTC로 조회됨
        assert positions["BTC-USDT"] == 0.5

    # ===== 가치 계산 테스트 =====

    def test_get_position_market_value(self, portfolio, market_data):
        """포지션의 현재 시장 가치 계산 테스트

        Given:
        - BTC 0.5개를 45,000 USDT/BTC에 매수 (총 22,500 USDT 지불)
        - 현재 시장 가격: 50,000 USDT/BTC

        When: get_position_market_value("BTC-USDT") 호출

        Then: 25,000 USDT 반환

        계산 과정:
        1. Portfolio에서 BTC-USDT 보유량 조회: 0.5 BTC
        2. MarketData에서 BTC/USDT 현재 가격 조회: 50,000 USDT
        3. Market Value = 0.5 × 50,000 = 25,000 USDT

        주요 검증:
        - ticker → symbol 변환 (BTC-USDT → BTC/USDT)
        - 현재 시장 가격 기준 계산 (매입가 45,000이 아님)
        """
        # Given: 45,000 USDT에 BTC 0.5개 매수
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,  # 매입가 (현재가 50,000과 다름)
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))  # 실제 지불 금액
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        position_manager = PositionManager(portfolio, market_data, initial_balance=10000.0)

        # When: 현재 시장 가치 조회
        market_value = position_manager.get_position_market_value("BTC-USDT")

        # Then: 현재 가격(50,000) 기준으로 계산됨
        # 계산: 0.5 BTC × 50,000 USDT/BTC = 25,000 USDT
        assert market_value == pytest.approx(25000.0)

    def test_get_position_book_value(self, portfolio, market_data):
        """포지션의 보유 가치 (매수 당시 금액) 계산 테스트

        Given: BTC 0.5개를 45,000 USDT/BTC에 매수 (총 22,500 USDT 지불)
        When: get_position_book_value("BTC-USDT") 호출
        Then: 22,500 USDT 반환

        계산 과정:
        1. Portfolio에서 BTC-USDT PairStack 조회
        2. PairStack.total_value_amount() 호출
        3. 매수 당시 지불한 총 금액 반환: 22,500 USDT

        주요 검증:
        - Book Value = 매수 당시 실제 지불 금액
        - 현재 시장 가격과 무관
        - PairStack에 저장된 value token의 총량
        """
        # Given: 45,000 USDT에 BTC 0.5개 매수
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))  # 실제 지불 금액
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        position_manager = PositionManager(portfolio, market_data, initial_balance=10000.0)

        # When: 보유 가치 조회
        book_value = position_manager.get_position_book_value("BTC-USDT")

        # Then: 매수 당시 지불한 금액 반환
        # Pair의 value token: Token("USDT", 22500.0)
        assert book_value == pytest.approx(22500.0)

    def test_get_position_market_value_no_price_data(self, portfolio, market_data):
        """가격 데이터가 없는 포지션의 시장 가치 조회 테스트

        Given: SOL/USDT 가격 데이터가 MarketData에 없음
        When: get_position_market_value("SOL-USDT") 호출
        Then: 0.0 반환

        예외 처리 검증:
        - 가격 데이터가 없어도 예외 발생하지 않음
        - 안전하게 0.0 반환
        """
        position_manager = PositionManager(portfolio, market_data, initial_balance=100000.0)

        # When: 가격 데이터 없는 SOL-USDT 시장 가치 조회
        market_value = position_manager.get_position_market_value("SOL-USDT")

        # Then: 0.0 반환 (예외 발생 안 함)
        assert market_value == 0.0

    def test_get_currency_value_usdt_only(self, portfolio, market_data):
        """Currency 총 가치 계산 테스트 (USDT만 보유)

        Given: USDT 100,000 보유
        When: get_currency_value("USDT") 호출
        Then: 100,000 USDT 반환

        계산 과정:
        1. Portfolio에서 모든 Currency 조회
        2. quote_currency와 동일한 Currency는 1:1 계산
        3. USDT: 100,000 × 1 = 100,000 USDT

        검증:
        - 기준 화폐(quote_currency)는 환산 없이 그대로 계산
        """
        position_manager = PositionManager(portfolio, market_data, initial_balance=100000.0)

        # When: USDT 기준 Currency 총 가치 조회
        value = position_manager.get_currency_value("USDT")

        # Then: USDT 잔고 그대로 반환
        assert value == pytest.approx(100000.0)

    def test_get_currency_value_multiple_currencies(self, portfolio, market_data):
        """Currency 총 가치 계산 테스트 (여러 통화 보유)

        Given:
        - USDT: 100,000
        - BTC: 0.2 (현재가: 50,000 USDT/BTC)

        When: get_currency_value("USDT") 호출

        Then: 110,000 USDT 반환

        계산 과정:
        1. USDT: 100,000 × 1 = 100,000 USDT (기준 화폐)
        2. BTC: 0.2 × 50,000 = 10,000 USDT (현재가로 환산)
        3. 총합: 100,000 + 10,000 = 110,000 USDT

        검증:
        - 다른 Currency는 현재 시장 가격으로 환산
        - symbol/quote 형식으로 가격 조회 (BTC/USDT)
        """
        # Given: BTC Currency 추가
        portfolio.deposit_currency("BTC", 0.2)

        position_manager = PositionManager(portfolio, market_data, initial_balance=100000.0)

        # When: USDT 기준 Currency 총 가치 조회
        value = position_manager.get_currency_value("USDT")

        # Then: 모든 Currency의 USDT 환산 가치 합산
        # USDT: 100,000
        # BTC: 0.2 × 50,000 = 10,000
        # 총: 110,000 USDT
        assert value == pytest.approx(110000.0)

    def test_get_total_value(self, portfolio, market_data):
        """총 자산 가치 계산 테스트 (Currency + Position)

        Given:
        - 초기 USDT: 100,000
        - BTC 포지션 매수: 0.5 BTC @ 45,000 USDT (지불: 22,500 USDT)
        - ETH 포지션 매수: 2.0 ETH @ 2,400 USDT (지불: 4,800 USDT)
        - 현재 가격: BTC 50,000 USDT, ETH 2,500 USDT

        When: get_total_value("USDT") 호출

        Then: 102,700 USDT 반환

        계산 과정:
        1. Currency USDT 잔고: 100,000 - 22,500 - 4,800 = 72,700 USDT
        2. BTC Position 현재 가치: 0.5 × 50,000 = 25,000 USDT
        3. ETH Position 현재 가치: 2.0 × 2,500 = 5,000 USDT
        4. 총 자산: 72,700 + 25,000 + 5,000 = 102,700 USDT

        검증:
        - Currency와 Position을 모두 포함한 총 자산 가치
        - Position은 현재 시장 가격으로 평가
        """
        # Given: BTC 포지션 생성 (0.5 BTC @ 45,000)
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)

        # ETH 포지션 생성 (2.0 ETH @ 2,400)
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_order = SpotOrder(
            order_id="order_2",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=2400.0,
            amount=2.0,
            timestamp=1000
        )
        eth_pair = Pair(Token("ETH", 2.0), Token("USDT", 4800.0))
        eth_trade = SpotTrade("trade_2", eth_order, eth_pair, 1000, None)

        # 충분한 자금으로 새 Portfolio 생성
        portfolio_new = Portfolio()
        portfolio_new.deposit_currency("USDT", 100000.0)
        portfolio_new.process_trade(trade)
        portfolio_new.process_trade(eth_trade)

        position_manager = PositionManager(portfolio_new, market_data, initial_balance=100000.0)

        # When: 총 자산 가치 조회
        total = position_manager.get_total_value("USDT")

        # Then: Currency + Position 현재 가치 합산
        # Currency USDT: 100,000 - 22,500 - 4,800 = 72,700
        # Position BTC: 0.5 × 50,000 = 25,000
        # Position ETH: 2.0 × 2,500 = 5,000
        # 총: 102,700 USDT
        assert total == pytest.approx(102700.0)

    # ===== 손익 계산 테스트 =====

    def test_get_total_pnl(self, portfolio, market_data):
        """전체 손익 계산 테스트 (손익 없음)

        Given:
        - 초기 자산: 100,000 USDT
        - 현재 자산: 100,000 USDT (거래 없음)

        When: get_total_pnl() 호출
        Then: 0 USDT 반환

        계산 과정:
        - PnL = 현재 총 자산 - 초기 자산
        - PnL = 100,000 - 100,000 = 0 USDT

        검증:
        - 거래가 없으면 손익도 0
        """
        position_manager = PositionManager(portfolio, market_data, initial_balance=100000.0)

        # When: 전체 손익 조회
        pnl = position_manager.get_total_pnl()

        # Then: 변동 없음
        # 현재 자산: 100,000 USDT
        # 초기 자산: 100,000 USDT
        # 손익: 0 USDT
        assert pnl == pytest.approx(0.0)

    def test_get_total_pnl_profit(self, portfolio, market_data):
        """전체 손익 계산 테스트 (이익 발생)

        Given:
        - 초기 자산: 100,000 USDT
        - BTC 0.5개를 45,000 USDT에 매수 (지불: 22,500 USDT)
        - 현재 BTC 가격: 50,000 USDT

        When: get_total_pnl() 호출
        Then: 2,500 USDT 반환

        계산 과정:
        1. Currency USDT: 100,000 - 22,500 = 77,500 USDT
        2. Position BTC 현재 가치: 0.5 × 50,000 = 25,000 USDT
        3. 현재 총 자산: 77,500 + 25,000 = 102,500 USDT
        4. PnL = 102,500 - 100,000 = 2,500 USDT (이익)

        검증:
        - 가격 상승으로 인한 이익 반영
        - 양수 = 이익
        """
        # Given: 충분한 자금으로 Portfolio 생성
        portfolio_new = Portfolio()
        portfolio_new.deposit_currency("USDT", 100000.0)

        # BTC 45,000 USDT에 0.5개 매수
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio_new.process_trade(trade)

        position_manager = PositionManager(portfolio_new, market_data, initial_balance=100000.0)

        # When: 전체 손익 조회
        pnl = position_manager.get_total_pnl()

        # Then: 가격 상승으로 이익 발생
        # Currency USDT: 100,000 - 22,500 = 77,500
        # Position BTC: 0.5 × 50,000 = 25,000 (현재 가격)
        # 현재 총 자산: 102,500
        # 손익: 102,500 - 100,000 = 2,500 USDT
        assert pnl == pytest.approx(2500.0)

    def test_get_total_pnl_ratio(self, portfolio, market_data):
        """전체 손익률 계산 테스트

        Given:
        - 초기 자산: 100,000 USDT
        - BTC 매수 후 2,500 USDT 이익 발생

        When: get_total_pnl_ratio() 호출
        Then: 2.5% 반환

        계산 과정:
        1. 현재 총 자산: 102,500 USDT
        2. 초기 자산: 100,000 USDT
        3. PnL Ratio = (102,500 - 100,000) / 100,000 × 100
        4. PnL Ratio = 2,500 / 100,000 × 100 = 2.5%

        검증:
        - 퍼센트 단위 반환
        - (현재 - 초기) / 초기 × 100
        """
        # Given: 이익이 발생한 Portfolio (이전 테스트와 동일)
        portfolio_new = Portfolio()
        portfolio_new.deposit_currency("USDT", 100000.0)

        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio_new.process_trade(trade)

        position_manager = PositionManager(portfolio_new, market_data, initial_balance=100000.0)

        # When: 전체 손익률 조회
        ratio = position_manager.get_total_pnl_ratio()

        # Then: 퍼센트로 반환
        # 손익: 2,500 USDT
        # 손익률: 2,500 / 100,000 × 100 = 2.5%
        assert ratio == pytest.approx(2.5)

    def test_get_total_pnl_ratio_zero_initial_balance(self, portfolio, market_data):
        """초기 자산이 0일 때 손익률 계산 테스트

        Given: 초기 자산 0 USDT
        When: get_total_pnl_ratio() 호출
        Then: 0.0 반환

        예외 처리 검증:
        - 초기 자산이 0이면 나누기 0 에러 방지
        - 안전하게 0.0 반환
        """
        position_manager = PositionManager(portfolio, market_data, initial_balance=0.0)

        # When: 초기 자산 0일 때 손익률 조회
        ratio = position_manager.get_total_pnl_ratio()

        # Then: 0.0 반환 (ZeroDivisionError 방지)
        assert ratio == 0.0

    # ===== 포지션별 손익 테스트 =====

    def test_get_position_pnl(self, portfolio, market_data):
        """포지션 손익 계산 테스트

        Given:
        - BTC 0.5개를 45,000 USDT에 매수 (지불: 22,500 USDT)
        - 현재 BTC 가격: 50,000 USDT

        When: get_position_pnl("BTC-USDT") 호출
        Then: 2,500 USDT 반환

        계산 과정:
        1. Market Value = 0.5 × 50,000 = 25,000 USDT
        2. Book Value = 22,500 USDT
        3. PnL = 25,000 - 22,500 = 2,500 USDT

        검증:
        - 포지션별 미실현 손익
        - 양수 = 이익 (현재가 > 평균 매입가)
        """
        # Given: BTC 포지션 생성
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)

        portfolio_new = Portfolio()
        portfolio_new.deposit_currency("USDT", 100000.0)
        portfolio_new.process_trade(trade)

        position_manager = PositionManager(portfolio_new, market_data, initial_balance=100000.0)

        # When: BTC 포지션 손익 조회
        pnl = position_manager.get_position_pnl("BTC-USDT")

        # Then: Market Value - Book Value
        # Market Value: 0.5 × 50,000 = 25,000
        # Book Value: 22,500
        # PnL: 25,000 - 22,500 = 2,500 USDT
        assert pnl == pytest.approx(2500.0)

    def test_get_position_pnl_ratio(self, portfolio, market_data):
        """포지션 손익률 계산 테스트

        Given:
        - BTC 0.5개를 45,000 USDT에 매수 (지불: 22,500 USDT)
        - 현재 BTC 가격: 50,000 USDT
        - 포지션 손익: 2,500 USDT

        When: get_position_pnl_ratio("BTC-USDT") 호출
        Then: 11.11% 반환

        계산 과정:
        1. Market Value = 25,000 USDT
        2. Book Value = 22,500 USDT
        3. PnL = 2,500 USDT
        4. PnL Ratio = 2,500 / 22,500 × 100 = 11.11%

        검증:
        - 포지션별 미실현 손익률
        - (Market Value - Book Value) / Book Value × 100
        """
        # Given: BTC 포지션 생성 (이전 테스트와 동일)
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)

        portfolio_new = Portfolio()
        portfolio_new.deposit_currency("USDT", 100000.0)
        portfolio_new.process_trade(trade)

        position_manager = PositionManager(portfolio_new, market_data, initial_balance=100000.0)

        # When: BTC 포지션 손익률 조회
        pnl_ratio = position_manager.get_position_pnl_ratio("BTC-USDT")

        # Then: 퍼센트로 반환
        # PnL: 2,500
        # Book Value: 22,500
        # PnL Ratio: 2,500 / 22,500 × 100 = 11.11%
        assert pnl_ratio == pytest.approx(11.11, abs=0.01)

    # ===== 자산 배분 통계 테스트 =====

    def test_get_position_allocation(self, portfolio, market_data):
        """자산별 비중 계산 테스트

        Given:
        - 초기 USDT: 100,000
        - BTC 포지션: 0.5 BTC (현재 가치: 25,000 USDT)
        - ETH 포지션: 2.0 ETH (현재 가치: 5,000 USDT)
        - 남은 USDT: 72,700
        - 총 자산: 102,700 USDT

        When: get_position_allocation() 호출

        Then: 각 자산의 비중(%) 반환

        계산 과정:
        1. 총 자산 = 72,700 + 25,000 + 5,000 = 102,700 USDT
        2. USDT 비중 = 72,700 / 102,700 × 100 = 70.79%
        3. BTC-USDT 비중 = 25,000 / 102,700 × 100 = 24.34%
        4. ETH-USDT 비중 = 5,000 / 102,700 × 100 = 4.87%

        검증:
        - Currency와 Position 모두 포함
        - 각 자산 가치 / 총 자산 가치 × 100
        - 모든 비중 합 = 100%
        """
        # Given: 다수 포지션 생성
        portfolio_new = Portfolio()
        portfolio_new.deposit_currency("USDT", 100000.0)

        # BTC 포지션
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=45000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 22500.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio_new.process_trade(trade)

        # ETH 포지션
        eth_address = StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m")
        eth_order = SpotOrder(
            order_id="order_2",
            stock_address=eth_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=2400.0,
            amount=2.0,
            timestamp=1000
        )
        eth_pair = Pair(Token("ETH", 2.0), Token("USDT", 4800.0))
        eth_trade = SpotTrade("trade_2", eth_order, eth_pair, 1000, None)
        portfolio_new.process_trade(eth_trade)

        position_manager = PositionManager(portfolio_new, market_data, initial_balance=100000.0)

        # When: 자산 배분 조회
        allocation = position_manager.get_position_allocation()

        # Then: 각 자산의 비중 반환
        # Currency USDT: 72,700 / 102,700 × 100 = 70.79%
        # Position BTC: 25,000 / 102,700 × 100 = 24.34%
        # Position ETH: 5,000 / 102,700 × 100 = 4.87%
        assert allocation["USDT"] == pytest.approx(70.79, abs=0.01)
        assert allocation["BTC-USDT"] == pytest.approx(24.34, abs=0.01)
        assert allocation["ETH-USDT"] == pytest.approx(4.87, abs=0.01)

    def test_get_position_allocation_zero_total(self):
        """총 자산이 0일 때 자산 배분 계산 테스트

        Given: 빈 포트폴리오 (총 자산 0)
        When: get_position_allocation() 호출
        Then: 빈 dict 반환

        예외 처리 검증:
        - 총 자산이 0이면 나누기 0 에러 방지
        - 안전하게 빈 dict 반환
        """
        portfolio_empty = Portfolio()
        data = {"BTC/USDT": [Price(o=50000, h=51000, l=48000, c=50000, v=100, t=1000, exchange="binance", market="spot")]}
        market_data = MarketData(data, availability_threshold=0.0, offset=0)
        market_data.reset()

        position_manager = PositionManager(portfolio_empty, market_data, initial_balance=0.0)

        # When: 빈 포트폴리오의 자산 배분 조회
        allocation = position_manager.get_position_allocation()

        # Then: 빈 dict 반환 (ZeroDivisionError 방지)
        assert allocation == {}

    # ===== 통합 시나리오 테스트 =====

    def test_currency_value_with_btc_currency(self, portfolio, market_data):
        """BTC Currency를 USDT로 환산하는 통합 테스트

        Given:
        - USDT: 100,000
        - BTC Currency: 0.1 (현재가: 50,000 USDT)

        When: get_currency_value("USDT") 호출
        Then: 105,000 USDT 반환

        계산 과정:
        1. USDT: 100,000 (기준 화폐, 환산 불필요)
        2. BTC: 0.1 × 50,000 = 5,000 USDT
        3. 총: 105,000 USDT

        검증:
        - Currency로 보유한 BTC도 현재가로 환산
        - Position이 아닌 Currency BTC 처리 확인
        """
        # Given: BTC Currency 추가
        portfolio.deposit_currency("BTC", 0.1)

        position_manager = PositionManager(portfolio, market_data, initial_balance=100000.0)

        # When: USDT 기준 Currency 총 가치 조회
        value = position_manager.get_currency_value("USDT")

        # Then: 모든 Currency 환산 가치 합산
        # USDT: 100,000
        # BTC: 0.1 × 50,000 = 5,000
        # 총: 105,000 USDT
        assert value == pytest.approx(105000.0)

    def test_ticker_to_symbol_conversion(self, portfolio, market_data):
        """ticker와 symbol 형식 변환 검증 테스트

        Given: BTC-USDT 포지션 보유
        When: get_position_market_value("BTC-USDT") 호출
        Then: BTC/USDT symbol로 변환하여 가격 조회 성공

        검증:
        - ticker 형식: "BTC-USDT" (하이픈)
        - symbol 형식: "BTC/USDT" (슬래시)
        - 내부적으로 자동 변환하여 가격 조회
        """
        # Given: BTC 포지션 생성
        stock_address = StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m")
        order = SpotOrder(
            order_id="order_1",
            stock_address=stock_address,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            price=50000.0,
            amount=0.5,
            timestamp=1000
        )
        pair = Pair(Token("BTC", 0.5), Token("USDT", 25000.0))
        trade = SpotTrade("trade_1", order, pair, 1000, None)
        portfolio.process_trade(trade)

        position_manager = PositionManager(portfolio, market_data, initial_balance=10000.0)

        # When: ticker 형식("BTC-USDT")으로 시장 가치 조회
        market_value = position_manager.get_position_market_value("BTC-USDT")

        # Then: symbol 형식("BTC/USDT")으로 자동 변환되어 가격 조회 성공
        # 0.5 BTC × 50,000 USDT = 25,000 USDT
        assert market_value == pytest.approx(25000.0)
