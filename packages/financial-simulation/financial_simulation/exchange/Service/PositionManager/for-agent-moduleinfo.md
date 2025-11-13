# PositionManager
포지션 조회 및 통계 제공 (Service Layer). Core 계층 계산 로직을 조합하여 다양한 포지션 통계를 제공.

_portfolio: Portfolio           # Portfolio 인스턴스
_market_data: MarketData        # MarketData 인스턴스
_initial_balance: float         # 초기 자산 (전체 손익률 계산용)
_value_calculator: ValueCalculator    # 가치 계산 Core
_pnl_calculator: PnLCalculator        # 손익 계산 Core

## 초기화

__init__(portfolio: Portfolio, market_data: MarketData, initial_balance: float) -> None
    PositionManager 초기화

    Args:
        portfolio: Portfolio 인스턴스
        market_data: MarketData 인스턴스 (현재 가격 조회용)
        initial_balance: 초기 자산 (전체 손익률 계산 기준)

## 포지션 조회

get_positions() -> dict[str, float]
    보유 포지션 조회 (Portfolio.get_positions() 래핑)

    Returns:
        dict[str, float]: {ticker: amount} 형식. 예: {"BTC-USDT": 0.5}

## 포지션 가치 계산

get_position_book_value(ticker: str) -> float
    특정 포지션의 보유 가치 (매수 당시 지불한 금액)

    Args:
        ticker: Position ticker (예: "BTC-USDT")

    Returns:
        float: 보유 가치 (quote 화폐 기준)

    Notes:
        - PairStack.total_value_amount() 사용
        - 평균 매입가 × 보유 수량과 동일
        - 포지션 없으면 0.0 반환

get_position_market_value(ticker: str) -> float
    특정 포지션의 현재 시장 가치 (현재 가격 기준)

    Args:
        ticker: Position ticker (예: "BTC-USDT")

    Returns:
        float: 현재 시장 가치 (quote 화폐 기준)

    Notes:
        - 현재 가격 × 보유 수량
        - ticker에서 symbol 추출하여 가격 조회 (BTC-USDT → BTC/USDT)
        - 가격 데이터 없으면 0.0 반환

get_currency_value(quote_currency: str = "USDT") -> float
    Currency 총 가치 계산 (모든 보유 화폐의 합산 가치)

    Args:
        quote_currency: 기준 화폐 (기본값: "USDT")

    Returns:
        float: Currency 총 가치 (quote_currency 기준)

    Notes:
        - quote_currency 자체는 1:1 계산
        - 다른 Currency는 현재 가격으로 환산
        - 예: USDT 10000 + BTC 0.1 * 50000 = 15000 USDT

get_total_value(quote_currency: str = "USDT") -> float
    총 자산 가치 계산 (Currency + Position 현재 가치)

    Args:
        quote_currency: 기준 화폐 (기본값: "USDT")

    Returns:
        float: 총 자산 가치 (quote_currency 기준)

    Notes:
        - Currency 가치 + 모든 Position의 현재 시장 가치
        - 가격 데이터 없는 자산은 0으로 처리

## 포지션 손익 계산

get_position_pnl(ticker: str) -> float
    특정 포지션의 미실현 손익 (절대값)

    Args:
        ticker: Position ticker (예: "BTC-USDT")

    Returns:
        float: 손익 (quote 화폐 기준)

    Notes:
        - 양수: 이익 (현재 가격이 평균 매입가보다 높음)
        - 음수: 손실 (현재 가격이 평균 매입가보다 낮음)
        - 계산: Market Value - Book Value

get_position_pnl_ratio(ticker: str) -> float
    특정 포지션의 미실현 손익률 (%)

    Args:
        ticker: Position ticker (예: "BTC-USDT")

    Returns:
        float: 손익률 (퍼센트 단위, 예: 10.5 = 10.5%)

    Notes:
        - (Market Value - Book Value) / Book Value * 100
        - Book Value가 0이면 0.0 반환

## 전체 손익 계산

get_total_pnl() -> float
    전체 손익 계산 (절대값)

    Returns:
        float: 현재 총 자산 - 초기 자산

    Notes:
        - 양수: 이익
        - 음수: 손실
        - 모든 Currency + Position 포함

get_total_pnl_ratio() -> float
    전체 손익률 계산 (%)

    Returns:
        float: (현재 총 자산 - 초기 자산) / 초기 자산 * 100

    Notes:
        - 반환값은 퍼센트 단위 (10.5 = 10.5%)
        - initial_balance가 0이면 0.0 반환

## 자산 배분 통계

get_position_allocation() -> dict[str, float]
    포지션별 자산 비중 계산 (%)

    Returns:
        dict[str, float]: {ticker/currency: 비중(%)} 형식

    Notes:
        - 각 포지션 시장 가치 / 총 자산 가치 * 100
        - Currency 잔고도 포함 (예: "USDT": 30.5)
        - 총 자산이 0이면 빈 dict 반환

---

**사용 예시:**
```python
# 초기화
position_manager = PositionManager(portfolio, market_data, initial_balance=100000.0)

# 포지션 조회
positions = position_manager.get_positions()  # {"BTC-USDT": 0.5, "ETH-USDT": 2.0}

# 포지션 가치
book_value = position_manager.get_position_book_value("BTC-USDT")     # 22500 USDT (매수 당시)
market_value = position_manager.get_position_market_value("BTC-USDT") # 25000 USDT (현재 가격)

# 포지션 손익
pnl = position_manager.get_position_pnl("BTC-USDT")         # 2500 USDT
pnl_ratio = position_manager.get_position_pnl_ratio("BTC-USDT")  # 11.11%

# 전체 자산
total = position_manager.get_total_value()  # 102500 USDT

# 전체 손익
total_pnl = position_manager.get_total_pnl()          # 2500 USDT
total_pnl_ratio = position_manager.get_total_pnl_ratio()  # 2.5%

# 자산 배분
allocation = position_manager.get_position_allocation()
# {"BTC-USDT": 24.39, "ETH-USDT": 4.88, "USDT": 70.73}
```

**의존성:**
- Portfolio: 잔고 및 포지션 데이터 조회
- MarketData: 현재 가격 정보 조회
- ValueCalculator (Core): 가치 계산 로직
- PnLCalculator (Core): 손익 계산 로직

**핵심 개념:**
- **Book Value (보유 가치)**: 매수 당시 지불한 금액 총합 (PairStack.total_value_amount())
- **Market Value (현재 가치)**: 현재 시장 가격 × 보유 수량
- **Unrealized PnL (미실현 손익)**: Market Value - Book Value
- **ticker 형식**: "BTC-USDT" → symbol 형식 "BTC/USDT"로 변환 필요
