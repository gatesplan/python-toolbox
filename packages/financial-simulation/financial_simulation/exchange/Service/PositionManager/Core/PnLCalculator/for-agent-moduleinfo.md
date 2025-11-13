# PnLCalculator
손익 및 통계 계산 로직 (Core Layer). Stateless 정적 메서드로 구성.

## 손익 계산

@staticmethod
calculate_pnl(market_value: float, book_value: float) -> float
    손익 계산 (절대값)

    Args:
        market_value: 현재 시장 가치
        book_value: 보유 가치 (매수 당시 금액)

    Returns:
        float: 손익 (market_value - book_value)

    Notes:
        - 양수: 이익 (현재 가격이 평균 매입가보다 높음)
        - 음수: 손실 (현재 가격이 평균 매입가보다 낮음)

@staticmethod
calculate_pnl_ratio(market_value: float, book_value: float) -> float
    손익률 계산 (%)

    Args:
        market_value: 현재 시장 가치
        book_value: 보유 가치 (매수 당시 금액)

    Returns:
        float: 손익률 (퍼센트 단위, 예: 10.5 = 10.5%)

    Notes:
        - (market_value - book_value) / book_value * 100
        - book_value가 0이면 0.0 반환

## 전체 손익 계산

@staticmethod
calculate_total_pnl(current_value: float, initial_balance: float) -> float
    전체 손익 계산 (절대값)

    Args:
        current_value: 현재 총 자산 가치
        initial_balance: 초기 자산

    Returns:
        float: 전체 손익 (current_value - initial_balance)

    Notes:
        - 양수: 이익
        - 음수: 손실

@staticmethod
calculate_total_pnl_ratio(current_value: float, initial_balance: float) -> float
    전체 손익률 계산 (%)

    Args:
        current_value: 현재 총 자산 가치
        initial_balance: 초기 자산

    Returns:
        float: 전체 손익률 (퍼센트 단위, 예: 10.5 = 10.5%)

    Notes:
        - (current_value - initial_balance) / initial_balance * 100
        - initial_balance가 0이면 0.0 반환

## 자산 배분 계산

@staticmethod
calculate_allocation(values: dict[str, float], total_value: float) -> dict[str, float]
    자산별 비중 계산 (%)

    Args:
        values: {ticker/currency: value} 형식
        total_value: 총 자산 가치

    Returns:
        dict[str, float]: {ticker/currency: 비중(%)} 형식

    Notes:
        - 각 자산 가치 / 총 자산 가치 * 100
        - total_value가 0이면 빈 dict 반환

---

**사용 예시:**
```python
# 포지션 손익
market_value = 25000.0  # 현재 가치
book_value = 22500.0    # 매수 당시 금액
pnl = PnLCalculator.calculate_pnl(market_value, book_value)  # 2500 USDT
pnl_ratio = PnLCalculator.calculate_pnl_ratio(market_value, book_value)  # 11.11%

# 전체 손익
current_value = 102500.0
initial_balance = 100000.0
total_pnl = PnLCalculator.calculate_total_pnl(current_value, initial_balance)  # 2500 USDT
total_pnl_ratio = PnLCalculator.calculate_total_pnl_ratio(current_value, initial_balance)  # 2.5%

# 자산 배분
values = {
    "BTC-USDT": 25000.0,
    "ETH-USDT": 5000.0,
    "USDT": 72500.0
}
total = 102500.0
allocation = PnLCalculator.calculate_allocation(values, total)
# {"BTC-USDT": 24.39, "ETH-USDT": 4.88, "USDT": 70.73}
```

**의존성:**
- 없음 (순수 계산 함수)

**계산 공식:**
- **PnL**: Market Value - Book Value
- **PnL Ratio**: (Market Value - Book Value) / Book Value × 100
- **Total PnL**: Current Value - Initial Balance
- **Total PnL Ratio**: (Current Value - Initial Balance) / Initial Balance × 100
- **Allocation**: Value / Total Value × 100
