# Core Layer (PositionManager)

PositionManager의 계산 로직을 담당하는 Core 계층. 모든 클래스는 Stateless 정적 메서드로 구성.

## ValueCalculator
자산 가치 계산 로직

calculate_position_book_value(pair_stack: PairStack | None) -> float
    포지션 보유 가치 계산 (매수 당시 금액)

calculate_position_market_value(amount: float, current_price: float) -> float
    포지션 현재 시장 가치 계산

calculate_currency_value(currencies: dict[str, float], quote_currency: str, market_data: MarketData) -> float
    Currency 총 가치 계산 (quote_currency 기준)

calculate_total_value(currency_value: float, position_market_values: dict[str, float]) -> float
    총 자산 가치 계산 (Currency + Position)

## PnLCalculator
손익 및 통계 계산 로직

calculate_pnl(market_value: float, book_value: float) -> float
    손익 계산 (절대값)

calculate_pnl_ratio(market_value: float, book_value: float) -> float
    손익률 계산 (%)

calculate_total_pnl(current_value: float, initial_balance: float) -> float
    전체 손익 계산 (절대값)

calculate_total_pnl_ratio(current_value: float, initial_balance: float) -> float
    전체 손익률 계산 (%)

calculate_allocation(values: dict[str, float], total_value: float) -> dict[str, float]
    자산별 비중 계산 (%)

---

**설계 원칙:**
- 모든 메서드는 정적 메서드 (@staticmethod)
- Stateless: 내부 상태 없음
- 순수 함수: 동일 입력 → 동일 출력
- 재사용성: Service에서 조합하여 사용

**책임 분리:**
- ValueCalculator: 가치 계산 (Book/Market Value)
- PnLCalculator: 손익 및 통계 계산 (PnL, Allocation)
