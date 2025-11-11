# Portfolio
거래소 맥락의 자산 관리. SpotWallet을 래핑하고 자산 예약(promise) 시스템을 제공하여 미체결 주문에 대한 자금 잠금을 관리합니다.

## 책임 범위
- 실제 자산 보유량 관리 (SpotWallet 위임)
- 미체결 주문을 위한 자산 예약 관리
- 사용 가능 잔고 계산 (총 잔고 - 예약 자산)
- 거래 처리 및 장부 기록 (SpotWallet 위임)

## 주요 속성

_wallet: SpotWallet                    # 실제 자산 보유 지갑
_promise_manager: PromiseManager       # 자산 예약 관리자

## 주요 메서드

### 잔고 관리

deposit_currency(symbol: str, amount: float) -> None
    화폐 입금

    Args:
        symbol: 화폐 심볼 (예: "USDT", "BTC")
        amount: 입금 수량

    Returns:
        None

withdraw_currency(symbol: str, amount: float) -> None
    화폐 출금

    Args:
        symbol: 화폐 심볼
        amount: 출금 수량

    Raises:
        ValueError: 사용 가능 잔고 부족 시

    Returns:
        None

get_balance(symbol: str) -> float
    총 잔고 조회 (예약 자산 포함)

    Args:
        symbol: 화폐 심볼

    Returns:
        float: 총 보유 수량

get_available_balance(symbol: str) -> float
    사용 가능 잔고 조회 (총 잔고 - 예약 자산)

    Args:
        symbol: 화폐 심볼

    Returns:
        float: 사용 가능 수량

get_locked_balance(symbol: str) -> float
    예약된 자산 수량 조회

    Args:
        symbol: 화폐 심볼

    Returns:
        float: 예약된 수량

### 자산 예약 (Promise)

lock_currency(promise_id: str, symbol: str, amount: float) -> None
    자산 예약 (미체결 주문용)

    Args:
        promise_id: 예약 식별자 (주문 ID 등)
        symbol: 화폐 심볼
        amount: 예약 수량

    Raises:
        ValueError: 사용 가능 잔고 부족 시

    Returns:
        None

unlock_currency(promise_id: str) -> None
    자산 예약 해제

    Args:
        promise_id: 예약 식별자

    Returns:
        None

### 거래 처리

process_trade(trade: SpotTrade) -> None
    거래 처리 (SpotWallet에 위임)
    BUY: quote 화폐 차감 + 자산 추가
    SELL: 자산 차감 + quote 화폐 증가

    Args:
        trade: 체결된 거래 객체

    Raises:
        ValueError: 잔고 부족 시

    Returns:
        None

### 조회

get_positions() -> dict[str, float]
    보유 포지션 조회 (ticker -> 자산 수량)

    Returns:
        dict[str, float]: {ticker: asset_amount}

get_currencies() -> list[str]
    보유 화폐 목록

    Returns:
        list[str]: 화폐 심볼 리스트

get_wallet() -> SpotWallet
    내부 SpotWallet 접근 (고급 기능용)

    Returns:
        SpotWallet: 내부 지갑 객체

---

# PromiseManager
자산 예약 관리자. 미체결 주문에 대한 자금 예약을 추적합니다.

## 책임 범위
- Promise 생성 및 삭제
- 화폐별 예약 수량 집계
- Promise 목록 조회

## 주요 속성

_promises: dict[str, dict]    # {promise_id: {symbol: str, amount: float}}

## 주요 메서드

lock(promise_id: str, symbol: str, amount: float) -> None
    자산 예약 생성

    Args:
        promise_id: 고유 식별자
        symbol: 화폐 심볼
        amount: 예약 수량

    Raises:
        ValueError: promise_id 중복 시

    Returns:
        None

unlock(promise_id: str) -> None
    자산 예약 삭제

    Args:
        promise_id: 예약 식별자

    Raises:
        KeyError: 존재하지 않는 promise_id

    Returns:
        None

get_locked_amount(symbol: str) -> float
    특정 화폐의 총 예약 수량 계산

    Args:
        symbol: 화폐 심볼

    Returns:
        float: 예약된 총 수량

get_promise(promise_id: str) -> dict | None
    특정 promise 조회

    Args:
        promise_id: 예약 식별자

    Returns:
        dict | None: {symbol: str, amount: float} 또는 None

get_all_promises() -> dict[str, dict]
    모든 promise 조회

    Returns:
        dict[str, dict]: {promise_id: {symbol: str, amount: float}}

---

## 사용 예시

```python
# Portfolio 생성
portfolio = Portfolio()

# 초기 입금
portfolio.deposit_currency("USDT", 10000.0)

# 주문 생성 시 자산 예약
order_id = "order_123"
portfolio.lock_currency(order_id, "USDT", 5000.0)

# 사용 가능 잔고 확인
available = portfolio.get_available_balance("USDT")  # 5000.0
total = portfolio.get_balance("USDT")                # 10000.0
locked = portfolio.get_locked_balance("USDT")        # 5000.0

# 주문 체결 시
trade = SpotTrade(...)  # 체결된 거래
portfolio.unlock_currency(order_id)      # 예약 해제
portfolio.process_trade(trade)           # 실제 자산 변경

# 주문 취소 시
portfolio.unlock_currency(order_id)      # 예약만 해제
```

## 설계 노트

**SpotWallet vs Portfolio:**
- **SpotWallet**: 순수 자산 보유 관리 (도메인: 지갑)
- **Portfolio**: 거래소 맥락의 자산 관리 (도메인: 거래소)
- Portfolio는 SpotWallet을 래핑하고 promise 시스템을 추가

**Promise 시스템:**
- 미체결 주문에 필요한 자금을 "예약"
- 실제 자산은 변경하지 않고 가용성만 제한
- 체결/취소 시 예약 해제 후 실제 처리
