"""자산 가치 계산 로직 (Core Layer)"""

from typing import Optional
from financial_assets.pair import PairStack
from financial_assets.symbol import Symbol
from financial_simulation.exchange.Core.MarketData.MarketData import MarketData


class ValueCalculator:
    """자산 가치 계산 로직. Stateless 정적 메서드로 구성."""

    @staticmethod
    def calculate_position_book_value(pair_stack: Optional[PairStack]) -> float:
        """포지션의 보유 가치 계산 (매수 당시 지불한 금액).

        Args:
            pair_stack: PairStack 인스턴스 (None 허용)

        Returns:
            float: 보유 가치 (PairStack.total_value_amount())

        Notes:
            - pair_stack이 None이거나 비어있으면 0.0 반환
            - Book Value = 매수 당시 지불한 총 금액
            - 평균 매입가 × 보유 수량과 동일
        """
        if pair_stack is None or pair_stack.is_empty():
            return 0.0

        return pair_stack.total_value_amount()

    @staticmethod
    def calculate_position_market_value(amount: float, current_price: float) -> float:
        """포지션의 현재 시장 가치 계산.

        Args:
            amount: 보유 수량
            current_price: 현재 시장 가격

        Returns:
            float: 현재 시장 가치 (amount × current_price)

        Notes:
            - amount나 current_price가 0이면 0.0 반환
            - Market Value = 현재 가격 × 보유 수량
        """
        if amount == 0 or current_price == 0:
            return 0.0

        return amount * current_price

    @staticmethod
    def calculate_currency_value(
        currencies: dict[str, float],
        quote_currency: str,
        market_data: MarketData
    ) -> float:
        """모든 Currency의 총 가치 계산 (quote_currency 기준).

        Args:
            currencies: {currency_symbol: amount} 형식
            quote_currency: 기준 화폐 (예: "USDT")
            market_data: MarketData 인스턴스 (현재 가격 조회용)

        Returns:
            float: Currency 총 가치 (quote_currency 기준)

        Notes:
            - quote_currency 자체는 1:1 계산
            - 다른 Currency는 symbol/quote_currency 형식으로 가격 조회
            - 예: BTC → BTC/USDT 가격 조회
            - 가격 데이터 없으면 해당 Currency는 0으로 처리
        """
        total_value = 0.0

        for currency_symbol, amount in currencies.items():
            if currency_symbol == quote_currency:
                # 기준 화폐는 1:1
                total_value += amount
            else:
                # 다른 화폐는 현재 가격으로 환산
                try:
                    symbol = Symbol(f"{currency_symbol}/{quote_currency}")
                    price_data = market_data.get_current(symbol)

                    if price_data is not None:
                        current_price = price_data.c
                        total_value += amount * current_price
                except ValueError:
                    # 잘못된 symbol 형식은 무시
                    pass
                # 가격 데이터 없으면 0으로 처리 (무시)

        return total_value

    @staticmethod
    def calculate_total_value(
        currency_value: float,
        position_market_values: dict[str, float]
    ) -> float:
        """총 자산 가치 계산 (Currency + Position).

        Args:
            currency_value: Currency 총 가치
            position_market_values: {ticker: market_value} 형식

        Returns:
            float: 총 자산 가치

        Notes:
            - 단순 합산: currency_value + sum(position_market_values.values())
        """
        position_value = sum(position_market_values.values())
        return currency_value + position_value
