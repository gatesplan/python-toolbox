# OrderBook
미체결 주문 관리. 주문 저장, 조회, 취소 및 TimeInForce 기반 자동 만료 처리를 담당합니다.

## 책임 범위
- 미체결 주문 저장 및 관리
- order_id 기반 주문 조회
- 심볼별 주문 목록 조회
- 주문 취소 (삭제)
- TimeInForce 기반 만료 주문 자동 제거

## 주요 속성

_orders: dict[str, SpotOrder]    # {order_id: order}
_symbol_index: dict[str, set[str]]    # {symbol: {order_id, ...}} 빠른 심볼별 조회

## 주요 메서드

### 주문 관리

add_order(order: SpotOrder) -> None
    미체결 주문 추가

    Args:
        order: 추가할 주문 객체

    Raises:
        ValueError: order_id 중복 시

    Returns:
        None

remove_order(order_id: str) -> None
    주문 제거 (취소)

    Args:
        order_id: 제거할 주문 ID

    Raises:
        KeyError: 존재하지 않는 order_id

    Returns:
        None

### 주문 조회

get_order(order_id: str) -> SpotOrder | None
    특정 주문 조회

    Args:
        order_id: 조회할 주문 ID

    Returns:
        SpotOrder | None: 주문 객체 또는 None

get_orders_by_symbol(symbol: str) -> list[SpotOrder]
    특정 심볼의 모든 미체결 주문 조회

    Args:
        symbol: 거래쌍 심볼 (예: "BTC/USDT")

    Returns:
        list[SpotOrder]: 해당 심볼의 주문 리스트

get_all_orders() -> list[SpotOrder]
    모든 미체결 주문 조회

    Returns:
        list[SpotOrder]: 전체 주문 리스트

get_order_count() -> int
    미체결 주문 총 개수

    Returns:
        int: 주문 개수

### 만료 처리

expire_orders(current_timestamp: int) -> list[str]
    TimeInForce 기반 만료 주문 제거

    Args:
        current_timestamp: 현재 시간 (timestamp)

    Returns:
        list[str]: 만료된 주문 ID 리스트

    Note:
        - TimeInForce.GTD (Good Till Date): expire_timestamp 초과 시 만료
        - TimeInForce.FOK (Fill Or Kill): 즉시 체결 실패 시 만료 (OrderExecutor에서 처리)
        - TimeInForce.IOC (Immediate Or Cancel): 부분 체결 후 즉시 만료 (OrderExecutor에서 처리)

---

## 사용 예시

```python
# OrderBook 생성
order_book = OrderBook()

# 주문 추가
order = SpotOrder(
    order_id="order_123",
    stock_address=StockAddress(...),
    side=Side.BUY,
    order_type=OrderType.LIMIT,
    price=50000.0,
    amount=0.1,
    timestamp=1000,
    time_in_force=TimeInForce.GTD,
    expire_timestamp=2000
)
order_book.add_order(order)

# 주문 조회
order = order_book.get_order("order_123")
btc_orders = order_book.get_orders_by_symbol("BTC/USDT")

# 만료 처리
expired_ids = order_book.expire_orders(current_timestamp=2500)

# 주문 취소
order_book.remove_order("order_123")
```

## 설계 노트

**심볼 인덱스:**
- 빠른 심볼별 조회를 위해 별도 인덱스 유지
- 주문 추가/삭제 시 인덱스 동기화

**TimeInForce 처리:**
- **GTD (Good Till Date)**: expire_timestamp로 만료 판단, expire_orders()에서 처리
- **FOK (Fill Or Kill)**: 즉시 체결 불가 시 주문 자체가 실패 (OrderExecutor에서 처리, OrderBook에 추가되지 않음)
- **IOC (Immediate Or Cancel)**: 부분 체결 후 미체결 수량 취소 (OrderExecutor에서 처리, OrderBook에 추가되지 않거나 즉시 제거)
- **GTC (Good Till Cancel)**: 취소 전까지 유효 (기본값, expire_timestamp=None)

**thread-safety:**
- 현재 구현은 단일 스레드 환경 가정
- 멀티스레드 필요 시 Lock 추가 필요
