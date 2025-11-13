# Portfolio
거래소 맥락의 자산 관리. SpotWallet 래핑 + Currency/Position 통합 잠금 시스템.

_wallet: SpotWallet
_promise_manager: PromiseManager

## Currency 관리

deposit_currency(symbol: str, amount: float) -> None
    화폐 입금

withdraw_currency(symbol: str, amount: float) -> None
    raise ValueError
    화폐 출금

get_balance(symbol: str) -> float
    총 Currency 잔고 조회 (잠금 포함)

get_available_balance(symbol: str) -> float
    사용 가능 Currency 잔고 (총 잔고 - 잠긴 잔고)

get_locked_balance(symbol: str) -> float
    잠긴 Currency 수량 조회

get_currencies() -> list[str]
    보유 Currency 목록

## Position 관리

get_positions() -> dict[str, float]
    보유 Position 조회 (ticker -> 자산 수량). 예: {"BTC-USDT": 10.0}

get_available_position(ticker: str) -> float
    사용 가능 Position 수량 (총 포지션 - 잠긴 포지션)

get_locked_position(ticker: str) -> float
    잠긴 Position 수량 조회

## 자산 잠금

lock_currency(promise_id: str, symbol: str, amount: float) -> None
    raise ValueError
    Currency 잠금 (BUY 주문 미체결용). 사용 가능 잔고 부족 시 예외

lock_position(promise_id: str, ticker: str, amount: float) -> None
    raise ValueError
    Position 잠금 (SELL 주문 미체결용). 사용 가능 포지션 부족 시 예외

unlock_currency(promise_id: str) -> None
    raise KeyError
    자산 잠금 해제 (Currency 및 Position 모두 지원). promise_id 미존재 시 예외

## 거래 처리

process_trade(trade: SpotTrade) -> None
    raise ValueError
    거래 처리 (BUY: quote 차감 + 자산 추가, SELL: 자산 차감 + quote 증가)

get_wallet() -> SpotWallet
    내부 SpotWallet 접근 (테스트용)

---

# PromiseManager
자산 잠금 관리자. Currency 및 Position 잠금 추적.

_promises: dict[str, Promise]    # {promise_id: Promise}

lock(promise_id: str, asset_type: AssetType, identifier: str, amount: float) -> None
    raise ValueError
    자산 잠금 생성. promise_id 중복 또는 amount <= 0 시 예외

unlock(promise_id: str) -> None
    raise KeyError
    자산 잠금 해제. promise_id 미존재 시 예외

get_locked_amount_by_type(asset_type: AssetType, identifier: str) -> float
    특정 타입 및 식별자의 총 잠금 수량

get_promise(promise_id: str) -> Promise | None
    Promise 조회

get_all_promises() -> dict[str, Promise]
    모든 Promise 조회

---

# InternalStruct

## Promise
자산 잠금 정보

promise_id: str          # 잠금 식별자 (주문 ID)
asset_type: AssetType    # 자산 타입 (CURRENCY or POSITION)
identifier: str          # Currency symbol 또는 Position ticker
amount: float            # 잠금 수량

## AssetType
자산 타입 enum

CURRENCY = "currency"    # Currency 잔고
POSITION = "position"    # Position (거래로 취득한 자산)

---

**Currency vs Position:**
- Currency: 입출금으로 관리되는 화폐 (예: USDT 100,000)
- Position: 거래로 생성/소멸되는 포지션 (예: BTC-USDT 10 BTC)
- BUY 거래 → quote Currency 차감, base Position 생성
- SELL 거래 → base Position 차감, quote Currency 증가

**자산 잠금 용도:**
- BUY 미체결: quote Currency 잠금 (USDT)
- SELL 미체결: base Position 잠금 (BTC-USDT)
- 주문 취소/체결 완료 시: unlock_currency()로 해제
