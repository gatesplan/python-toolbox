"""손익 및 통계 계산 로직 (Core Layer)"""


class PnLCalculator:
    """손익 및 통계 계산 로직. Stateless 정적 메서드로 구성."""

    @staticmethod
    def calculate_pnl(market_value: float, book_value: float) -> float:
        """손익 계산 (절대값).

        Args:
            market_value: 현재 시장 가치
            book_value: 보유 가치 (매수 당시 금액)

        Returns:
            float: 손익 (market_value - book_value)

        Notes:
            - 양수: 이익 (현재 가격이 평균 매입가보다 높음)
            - 음수: 손실 (현재 가격이 평균 매입가보다 낮음)
        """
        return market_value - book_value

    @staticmethod
    def calculate_pnl_ratio(market_value: float, book_value: float) -> float:
        """손익률 계산 (%).

        Args:
            market_value: 현재 시장 가치
            book_value: 보유 가치 (매수 당시 금액)

        Returns:
            float: 손익률 (퍼센트 단위, 예: 10.5 = 10.5%)

        Notes:
            - (market_value - book_value) / book_value * 100
            - book_value가 0이면 0.0 반환
        """
        if book_value == 0:
            return 0.0

        pnl = market_value - book_value
        return (pnl / book_value) * 100

    @staticmethod
    def calculate_total_pnl(current_value: float, initial_balance: float) -> float:
        """전체 손익 계산 (절대값).

        Args:
            current_value: 현재 총 자산 가치
            initial_balance: 초기 자산

        Returns:
            float: 전체 손익 (current_value - initial_balance)

        Notes:
            - 양수: 이익
            - 음수: 손실
        """
        return current_value - initial_balance

    @staticmethod
    def calculate_total_pnl_ratio(current_value: float, initial_balance: float) -> float:
        """전체 손익률 계산 (%).

        Args:
            current_value: 현재 총 자산 가치
            initial_balance: 초기 자산

        Returns:
            float: 전체 손익률 (퍼센트 단위, 예: 10.5 = 10.5%)

        Notes:
            - (current_value - initial_balance) / initial_balance * 100
            - initial_balance가 0이면 0.0 반환
        """
        if initial_balance == 0:
            return 0.0

        pnl = current_value - initial_balance
        return (pnl / initial_balance) * 100

    @staticmethod
    def calculate_allocation(values: dict[str, float], total_value: float) -> dict[str, float]:
        """자산별 비중 계산 (%).

        Args:
            values: {ticker/currency: value} 형식
            total_value: 총 자산 가치

        Returns:
            dict[str, float]: {ticker/currency: 비중(%)} 형식

        Notes:
            - 각 자산 가치 / 총 자산 가치 * 100
            - total_value가 0이면 빈 dict 반환
        """
        if total_value == 0:
            return {}

        allocation = {}
        for key, value in values.items():
            allocation[key] = (value / total_value) * 100

        return allocation
