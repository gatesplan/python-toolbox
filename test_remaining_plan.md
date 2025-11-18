# 나머지 메서드 테스트 계획

## 현재 상태
- 테스트 완료: 24/40 (60%)
  - Comprehensive test: 21개
  - 이전 테스트: 3개 (get_account, get_ticker_24hr, create_order MARKET)

## 남은 메서드: 16개

---

## Phase 8: OCO Order Test (우선순위: 높음)
**목적**: OCO 주문 생성/조회/취소 테스트

### 8.1 create_oco_order
- 목적: OCO 주문 생성 (익절/손절 자동화)
- 의존성: 현재가 조회, 충분한 XRP 잔고
- 위험도: 중간 (실제 체결 가능하지만 가격 조정으로 회피)
- 테스트:
  ```
  현재가: 2.17 USDT
  quantity: 5 XRP
  price (익절): 3.0 USDT (현재가 * 1.38)
  stopPrice (손절): 1.5 USDT (현재가 * 0.69)
  ```
- 예상 결과: orderListId 반환, status=EXECUTING

### 8.2 get_order_list
- 목적: 생성한 OCO 주문 조회
- 의존성: Phase 8.1의 orderListId
- 위험도: 없음 (읽기)
- 테스트: orderListId로 조회
- 예상 결과: 2개 주문 정보 (LIMIT + STOP_LOSS_LIMIT)

### 8.3 get_all_order_list
- 목적: 전체 OCO 주문 내역 조회
- 의존성: Phase 8.1 완료
- 위험도: 없음 (읽기)
- 테스트: limit=10
- 예상 결과: 방금 생성한 OCO 포함

### 8.4 get_open_order_list
- 목적: 현재 미체결 OCO 주문 조회
- 의존성: Phase 8.1의 OCO가 아직 미체결
- 위험도: 없음 (읽기)
- 테스트: 파라미터 없음
- 예상 결과: 방금 생성한 OCO 포함

### 8.5 cancel_order_list
- 목적: OCO 주문 취소
- 의존성: Phase 8.1의 orderListId
- 위험도: 중간 (취소 후 복구 불가)
- 테스트: orderListId로 취소
- 예상 결과: 2개 주문 모두 CANCELED

---

## Phase 9: Additional Market Data (우선순위: 중간)
**목적**: 추가 시장 데이터 메서드 테스트

### 9.1 get_historical_trades
- 목적: 과거 거래 내역 조회 (API 키 필요)
- 의존성: 없음
- 위험도: 없음 (읽기)
- 테스트: XRPUSDT, limit=10
- 예상 결과: 성공 또는 권한 오류 (-2014)
- 참고: 실패해도 OK (권한 문제일 수 있음)

### 9.2 get_aggregate_trades
- 목적: 압축된 거래 내역 조회
- 의존성: 없음
- 위험도: 없음 (읽기)
- 테스트: XRPUSDT, limit=10
- 예상 결과: 압축된 거래 내역 리스트

### 9.3 get_ui_klines
- 목적: UI 최적화 캔들 데이터
- 의존성: 없음
- 위험도: 없음 (읽기)
- 테스트: XRPUSDT, interval="1h", limit=5
- 예상 결과: get_klines와 유사한 데이터

### 9.4 get_rolling_window_ticker
- 목적: 롤링 윈도우 티커 (커스텀 시간 범위)
- 의존성: 없음
- 위험도: 없음 (읽기)
- 테스트: XRPUSDT, windowSize="1h"
- 예상 결과: 1시간 기준 통계

---

## Phase 10: Order Management Advanced (우선순위: 중간)
**목적**: 고급 주문 관리 기능 테스트

### 10.1 get_rate_limit_order
- 목적: 현재 주문 레이트 리밋 사용량 조회
- 의존성: 없음
- 위험도: 없음 (읽기)
- 테스트: 파라미터 없음
- 예상 결과: 각 시간대별 주문 개수
- 참고: 현재 사용량 모니터링에 유용

### 10.2 cancel_replace_order
- 목적: 주문 취소 후 새 주문 생성 (원자적)
- 의존성: 기존 LIMIT 주문 필요
- 위험도: 중간 (실제 주문 영향)
- 테스트:
  1. LIMIT 주문 생성 (price: 현재가 * 1.5)
  2. cancel_replace로 가격 변경 (price: 현재가 * 1.6)
  3. 새 주문 확인 후 취소
- 예상 결과: 기존 주문 취소 + 새 주문 생성

### 10.3 get_my_prevented_matches
- 목적: Self-trade prevention으로 방지된 매칭 조회
- 의존성: 없음 (없으면 빈 리스트)
- 위험도: 없음 (읽기)
- 테스트: XRPUSDT, limit=10
- 예상 결과: 빈 리스트 (일반적으로)

### 10.4 get_my_allocations
- 목적: SOR 할당 내역 조회
- 의존성: SOR 주문 사용 시에만 데이터 존재
- 위험도: 없음 (읽기)
- 테스트: XRPUSDT, limit=10
- 예상 결과: 빈 리스트 (SOR 미사용 시)

---

## Phase 11: Complex Orders (우선순위: 낮음)
**목적**: 복잡한 주문 유형 테스트 (선택적)

### 11.1 test_sor_order
- 목적: SOR 주문 검증 (실제 주문 X)
- 의존성: 없음
- 위험도: 없음 (실제 주문 안됨)
- 테스트: XRPUSDT, SELL, MARKET, quantity=5
- 예상 결과: 유효성 검증 통과

### 11.2 create_sor_order (선택적)
- 목적: SOR 주문 생성
- 의존성: 없음
- 위험도: 높음 (실제 체결 가능)
- 테스트: 신중히 결정
- 참고: 일반 주문으로 충분하면 SKIP

### 11.3 create_oto_order (선택적)
- 목적: OTO 주문 생성
- 의존성: 복잡한 파라미터 구조
- 위험도: 높음 (실제 체결 가능)
- 테스트: 신중히 결정
- 참고: OCO로 충분하면 SKIP

### 11.4 create_otoco_order (선택적)
- 목적: OTOCO 주문 생성
- 의존성: 매우 복잡한 파라미터 구조
- 위험도: 높음 (실제 체결 가능)
- 테스트: 신중히 결정
- 참고: OCO로 충분하면 SKIP

---

## 테스트하지 않을 메서드 (3개)

### cancel_open_orders
- 이유: 너무 위험 (심볼의 모든 주문 취소)
- 대안: cancel_order로 개별 취소 테스트 완료

### User Data Stream (3개)
- create_listen_key
- keep_alive_listen_key
- close_listen_key
- 이유: 웹소켓 연동 필요, 별도 프로젝트로 진행
- 참고: REST API 테스트 범위 밖

---

## 최종 테스트 순서

**Phase 8 (필수, 5개)**: OCO 주문 플로우
1. create_oco_order
2. get_order_list
3. get_all_order_list
4. get_open_order_list
5. cancel_order_list

**Phase 9 (권장, 4개)**: 추가 시장 데이터
6. get_historical_trades (실패 가능)
7. get_aggregate_trades
8. get_ui_klines
9. get_rolling_window_ticker

**Phase 10 (권장, 4개)**: 고급 주문 관리
10. get_rate_limit_order
11. cancel_replace_order
12. get_my_prevented_matches
13. get_my_allocations

**Phase 11 (선택, 1~4개)**: 복잡한 주문
14. test_sor_order (권장)
15. create_sor_order (선택)
16. create_oto_order (선택)
17. create_otoco_order (선택)

---

## 예상 최종 커버리지

- **Phase 8만 완료**: 29/40 (72.5%)
- **Phase 8+9 완료**: 33/40 (82.5%)
- **Phase 8+9+10 완료**: 37/40 (92.5%)
- **Phase 8+9+10+11(일부) 완료**: 38~40/40 (95~100%)

**제외**: cancel_open_orders (1개), User Data Stream (3개)

---

## 다음 단계

1. Phase 8 테스트 스크립트 작성 (OCO 주문)
2. Phase 9 테스트 스크립트 작성 (추가 시장 데이터)
3. Phase 10 테스트 스크립트 작성 (고급 주문 관리)
4. Phase 11은 사용자와 논의 후 결정
