# OrderBook
미체결 주문 관리. 주문 저장, 조회, 취소 및 TimeInForce 기반 자동 만료 처리.

_orders: dict[str, SpotOrder]
_symbol_index: dict[str, set[str]]    # {symbol: {order_id, ...}} 빠른 심볼별 조회

add_order(order: SpotOrder) -> None
    raise ValueError
    미체결 주문 추가

remove_order(order_id: str) -> None
    raise KeyError
    주문 제거 (취소)

get_order(order_id: str) -> SpotOrder | None
    특정 주문 조회

get_orders_by_symbol(symbol: str | Symbol) -> list[SpotOrder]
    특정 심볼의 모든 미체결 주문 조회

get_all_orders() -> list[SpotOrder]
    모든 미체결 주문 조회

get_order_count() -> int
    미체결 주문 총 개수

expire_orders(current_timestamp: int) -> list[str]
    TimeInForce 기반 만료 주문 제거 (GTD 처리)

---

## Symbol 지원

`get_orders_by_symbol()` 메서드는 `str | Symbol` 타입 지원:
- str: "BTC/USDT" (slash 형식)
- Symbol: Symbol("BTC/USDT") 또는 Symbol("BTC-USDT")

내부 변환:
- `str(symbol)` → "BTC/USDT" (_symbol_index 키 접근용)

---

**TimeInForce 처리:**
- GTD: expire_timestamp로 만료 판단, expire_orders()에서 처리
- FOK: 즉시 체결 불가 시 주문 실패 (OrderExecutor에서 처리, OrderBook에 추가되지 않음)
- IOC: 부분 체결 후 미체결 수량 취소 (OrderExecutor에서 처리)
- GTC: 취소 전까지 유효 (기본값, expire_timestamp=None)
