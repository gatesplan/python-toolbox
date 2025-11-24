# OrderHistory
모든 주문의 생성/체결/취소 상태 이력 관리. OrderBook과 달리 체결/취소된 주문도 보관.

_records: dict[str, OrderRecord]    # order_id → OrderRecord

## OrderRecord (Particles)

@dataclass(frozen=True)
order: SpotOrder
status: OrderStatus
timestamp: int    # 상태 변경 시각

## Methods

add_record(order: SpotOrder, status: OrderStatus, timestamp: int) -> None
    주문 이력 추가. 동일한 order_id는 덮어쓰기 (최신 상태 유지).

    Args:
        order: 주문 객체
        status: 주문 상태 (NEW, PARTIALLY_FILLED, FILLED, CANCELED, EXPIRED)
        timestamp: 상태 변경 시각

get_record(order_id: str) -> OrderRecord | None
    특정 주문 이력 조회

get_all_records() -> list[OrderRecord]
    모든 주문 이력 조회

get_records_by_status(status: OrderStatus) -> list[OrderRecord]
    상태별 주문 이력 조회

---

**책임:**
- 모든 주문의 상태 변경 이력 보관
- OrderBook에서 제거된 주문도 영구 보관
- 주문 상태별 필터링 조회 지원

**OrderBook과의 차이:**
- **OrderBook**: 미체결 주문만 관리, 체결/취소 시 즉시 삭제
- **OrderHistory**: 모든 주문 영구 보관, 상태 추적

**사용 시나리오:**
1. 주문 생성 시: NEW 상태로 이력 추가
2. 부분 체결 시: PARTIALLY_FILLED 상태로 갱신
3. 완전 체결 시: FILLED 상태로 갱신
4. 취소 시: CANCELED 상태로 갱신
5. 만료 시: EXPIRED 상태로 갱신

**OrderStatus (financial-assets.constants):**
- NEW: 주문 생성
- PARTIALLY_FILLED: 부분 체결
- FILLED: 완전 체결
- CANCELED: 사용자 취소
- EXPIRED: 만료 (GTD)
