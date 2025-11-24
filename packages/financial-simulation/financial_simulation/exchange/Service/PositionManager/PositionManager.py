"""포지션 조회 및 통계 제공 (Service Layer)"""

from financial_simulation.exchange.Core.Portfolio.Portfolio import Portfolio
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData
from financial_assets.symbol import Symbol
from .Core.ValueCalculator.ValueCalculator import ValueCalculator
from .Core.PnLCalculator.PnLCalculator import PnLCalculator
from simple_logger import init_logging, logger


class PositionManager:
    """포지션 조회 및 통계 제공.

    Core 계층 계산 로직을 조합하여 다양한 포지션 통계를 제공합니다.
    """

    @init_logging(level="INFO")
    def __init__(
        self,
        portfolio: Portfolio,
        market_data: MarketData,
        initial_balance: float
    ) -> None:
        """PositionManager 초기화.

        Args:
            portfolio: Portfolio 인스턴스
            market_data: MarketData 인스턴스 (현재 가격 조회용)
            initial_balance: 초기 자산 (전체 손익률 계산 기준)
        """
        self._portfolio = portfolio
        self._market_data = market_data
        self._initial_balance = initial_balance

        logger.info(f"PositionManager 초기화 완료: initial_balance={initial_balance}")

    # ===== 포지션 조회 =====

    def get_positions(self) -> dict[str, float]:
        """보유 포지션 조회 (Portfolio.get_positions() 래핑).

        Returns:
            dict[str, float]: {ticker: amount} 형식. 예: {"BTC-USDT": 0.5}
        """
        return self._portfolio.get_positions()

    # ===== 포지션 가치 계산 =====

    def get_position_book_value(self, ticker: str) -> float:
        """특정 포지션의 보유 가치 (매수 당시 지불한 금액).

        Args:
            ticker: Position ticker (예: "BTC-USDT")

        Returns:
            float: 보유 가치 (quote 화폐 기준)

        Notes:
            - PairStack.total_value_amount() 사용
            - 평균 매입가 × 보유 수량과 동일
            - 포지션 없으면 0.0 반환
        """
        pair_stack = self._portfolio.get_wallet().get_pair_stack(ticker)
        return ValueCalculator.calculate_position_book_value(pair_stack)

    def get_position_market_value(self, ticker: str) -> float:
        """특정 포지션의 현재 시장 가치 (현재 가격 기준).

        Args:
            ticker: Position ticker (예: "BTC-USDT")

        Returns:
            float: 현재 시장 가치 (quote 화폐 기준)

        Notes:
            - 현재 가격 × 보유 수량
            - ticker에서 symbol 추출하여 가격 조회 (BTC-USDT → BTC/USDT)
            - 가격 데이터 없으면 0.0 반환
        """
        # 포지션 수량 조회
        positions = self.get_positions()
        amount = positions.get(ticker, 0.0)

        if amount == 0:
            return 0.0

        # ticker → Symbol 객체로 변환 (BTC-USDT → Symbol)
        try:
            symbol = Symbol(ticker)
        except ValueError:
            # 잘못된 ticker 형식
            return 0.0

        price_data = self._market_data.get_current(symbol)

        if price_data is None:
            return 0.0

        current_price = price_data.c
        return ValueCalculator.calculate_position_market_value(amount, current_price)

    def get_currency_value(self, quote_currency: str = "USDT") -> float:
        """Currency 총 가치 계산 (모든 보유 화폐의 합산 가치).

        Args:
            quote_currency: 기준 화폐 (기본값: "USDT")

        Returns:
            float: Currency 총 가치 (quote_currency 기준)

        Notes:
            - quote_currency 자체는 1:1 계산
            - 다른 Currency는 현재 가격으로 환산
            - 예: USDT 10000 + BTC 0.1 * 50000 = 15000 USDT
        """
        # Currency 목록 및 잔고 조회
        currencies = {}
        for currency_symbol in self._portfolio.get_currencies():
            balance = self._portfolio.get_balance(currency_symbol)
            if balance > 0:
                currencies[currency_symbol] = balance

        return ValueCalculator.calculate_currency_value(
            currencies, quote_currency, self._market_data
        )

    def get_total_value(self, quote_currency: str = "USDT") -> float:
        """총 자산 가치 계산 (Currency + Position 현재 가치).

        Args:
            quote_currency: 기준 화폐 (기본값: "USDT")

        Returns:
            float: 총 자산 가치 (quote_currency 기준)

        Notes:
            - Currency 가치 + 모든 Position의 현재 시장 가치
            - 가격 데이터 없는 자산은 0으로 처리
        """
        # Currency 가치
        currency_value = self.get_currency_value(quote_currency)

        # 모든 Position의 현재 시장 가치
        position_market_values = {}
        positions = self.get_positions()

        for ticker in positions.keys():
            market_value = self.get_position_market_value(ticker)
            position_market_values[ticker] = market_value

        # 총 자산 가치
        return ValueCalculator.calculate_total_value(
            currency_value, position_market_values
        )

    # ===== 포지션 손익 계산 =====

    def get_position_pnl(self, ticker: str) -> float:
        """특정 포지션의 미실현 손익 (절대값).

        Args:
            ticker: Position ticker (예: "BTC-USDT")

        Returns:
            float: 손익 (quote 화폐 기준)

        Notes:
            - 양수: 이익 (현재 가격이 평균 매입가보다 높음)
            - 음수: 손실 (현재 가격이 평균 매입가보다 낮음)
            - 계산: Market Value - Book Value
        """
        market_value = self.get_position_market_value(ticker)
        book_value = self.get_position_book_value(ticker)

        return PnLCalculator.calculate_pnl(market_value, book_value)

    def get_position_pnl_ratio(self, ticker: str) -> float:
        """특정 포지션의 미실현 손익률 (%).

        Args:
            ticker: Position ticker (예: "BTC-USDT")

        Returns:
            float: 손익률 (퍼센트 단위, 예: 10.5 = 10.5%)

        Notes:
            - (Market Value - Book Value) / Book Value * 100
            - Book Value가 0이면 0.0 반환
        """
        market_value = self.get_position_market_value(ticker)
        book_value = self.get_position_book_value(ticker)

        return PnLCalculator.calculate_pnl_ratio(market_value, book_value)

    # ===== 전체 손익 계산 =====

    def get_total_pnl(self) -> float:
        """전체 손익 계산 (절대값).

        Returns:
            float: 현재 총 자산 - 초기 자산

        Notes:
            - 양수: 이익
            - 음수: 손실
            - 모든 Currency + Position 포함
        """
        current_value = self.get_total_value()
        return PnLCalculator.calculate_total_pnl(current_value, self._initial_balance)

    def get_total_pnl_ratio(self) -> float:
        """전체 손익률 계산 (%).

        Returns:
            float: (현재 총 자산 - 초기 자산) / 초기 자산 * 100

        Notes:
            - 반환값은 퍼센트 단위 (10.5 = 10.5%)
            - initial_balance가 0이면 0.0 반환
        """
        current_value = self.get_total_value()
        return PnLCalculator.calculate_total_pnl_ratio(current_value, self._initial_balance)

    # ===== 자산 배분 통계 =====

    def get_position_allocation(self) -> dict[str, float]:
        """포지션별 자산 비중 계산 (%).

        Returns:
            dict[str, float]: {ticker/currency: 비중(%)} 형식

        Notes:
            - 각 포지션 시장 가치 / 총 자산 가치 * 100
            - Currency 잔고도 포함 (예: "USDT": 30.5)
            - 총 자산이 0이면 빈 dict 반환
        """
        total_value = self.get_total_value()

        if total_value == 0:
            return {}

        # 모든 자산 가치 수집
        values = {}

        # Currency 가치
        for currency_symbol in self._portfolio.get_currencies():
            balance = self._portfolio.get_balance(currency_symbol)
            if balance > 0:
                # Currency를 quote로 변환한 가치 계산
                currencies = {currency_symbol: balance}
                currency_value = ValueCalculator.calculate_currency_value(
                    currencies, "USDT", self._market_data
                )
                if currency_value > 0:
                    values[currency_symbol] = currency_value

        # Position 가치
        positions = self.get_positions()
        for ticker in positions.keys():
            market_value = self.get_position_market_value(ticker)
            if market_value > 0:
                values[ticker] = market_value

        # 비중 계산
        return PnLCalculator.calculate_allocation(values, total_value)

    def __repr__(self) -> str:
        """상세한 문자열 표현 반환."""
        positions_count = len(self.get_positions())
        currencies_count = len(self._portfolio.get_currencies())
        total_value = self.get_total_value()

        return (
            f"PositionManager(currencies={currencies_count}, "
            f"positions={positions_count}, total_value={total_value:.2f})"
        )
