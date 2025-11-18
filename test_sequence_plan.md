# throttled-api 메서드 테스트 순서

## 현재 상태
- ✓ get_account (계정 조회)
- ✓ get_ticker_24hr (시세 조회)
- ✓ create_order MARKET (시장가 주문 - 이미 2개 체결됨)
  - 주문 ID: 13268822197 (SELL), 13268822401 (BUY)

---

## Phase 1: General - 기본 연결 확인 (의존성 없음)

### 1.1 ping
- 목적: API 연결 상태 확인
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 1

### 1.2 get_server_time
- 목적: 서버 시간 확인 (타임스탬프 동기화)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 1

### 1.3 get_exchange_info
- 목적: 거래소 정보, 심볼 정보, 제약사항 확인
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 20 (전체), 4 (단일 심볼)
- 참고: XRPUSDT의 LOT_SIZE, MIN_NOTIONAL 등 확인 가능

---

## Phase 2: Market Data - 시장 데이터 조회 (읽기 전용)

### 2.1 get_ticker_price
- 목적: 현재가 간단 조회 (get_ticker_24hr보다 가벼움)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 2 (단일), 4 (전체)

### 2.2 get_orderbook_ticker
- 목적: 호가 최우선가 (최고 매수가, 최저 매도가)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 2 (단일), 4 (전체)

### 2.3 get_order_book
- 목적: 호가창 조회 (depth)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 5 (limit 100), 25 (500), 50 (1000), 250 (5000)
- 테스트: limit=100 정도로

### 2.4 get_klines
- 목적: 캔들스틱 데이터 (OHLCV)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 2
- 테스트: XRPUSDT, interval="1h", limit=10

### 2.5 get_recent_trades
- 목적: 최근 체결 내역 (공개)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 25
- 테스트: XRPUSDT, limit=10

### 2.6 get_avg_price
- 목적: 평균가 조회 (5분)
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 2

---

## Phase 3: Account History - 과거 데이터 조회 (방금 생성한 주문 활용)

### 3.1 get_my_trades
- 목적: 내 체결 내역 확인
- 의존성: 이미 체결된 거래 필요 (✓ 있음)
- 위험도: 없음 (읽기)
- Weight: 20
- 테스트: XRPUSDT, limit=10
- 확인: 방금 체결된 주문 ID 13268822197, 13268822401 확인 가능

### 3.2 get_all_orders
- 목적: 전체 주문 내역 (체결/미체결/취소 모두)
- 의존성: 이미 주문 생성됨 (✓ 있음)
- 위험도: 없음 (읽기)
- Weight: 20
- 테스트: XRPUSDT, limit=10
- 확인: 주문 ID 13268822197, 13268822401 포함 여부

### 3.3 get_order (과거 주문)
- 목적: 특정 주문 상세 조회
- 의존성: 주문 ID 필요 (✓ 있음)
- 위험도: 없음 (읽기)
- Weight: 4
- 테스트: order_id=13268822197로 조회
- 확인: status=FILLED, executedQty 등

---

## Phase 4: Current State - 현재 상태 조회

### 4.1 get_open_orders
- 목적: 현재 미체결 주문 확인
- 의존성: 없음 (없으면 빈 리스트)
- 위험도: 없음 (읽기)
- Weight: 6 (단일 심볼), 80 (전체)
- 테스트: XRPUSDT로 조회
- 예상: 빈 리스트 (방금 주문은 모두 FILLED)

### 4.2 get_account_commission
- 목적: 심볼별 수수료율 확인
- 의존성: 없음
- 위험도: 없음 (읽기)
- Weight: 20
- 테스트: XRPUSDT

---

## Phase 5: Order Validation - 주문 검증 (실제 주문 안됨)

### 5.1 test_order (MARKET)
- 목적: 시장가 주문 유효성 검증 (실제 주문 X)
- 의존성: 없음
- 위험도: 없음 (실제 주문 안됨)
- Weight: 1
- 테스트: XRPUSDT, SELL, MARKET, quantity=1

### 5.2 test_order (LIMIT)
- 목적: 지정가 주문 유효성 검증
- 의존성: 없음
- 위험도: 없음 (실제 주문 안됨)
- Weight: 1
- 테스트: XRPUSDT, SELL, LIMIT, quantity=1, price=3.0 (현재가보다 높게)

---

## Phase 6: Order Creation (LIMIT) - 취소 가능한 주문 생성

### 6.1 create_order (LIMIT SELL)
- 목적: 지정가 매도 주문 생성 (높은 가격으로 체결 안되게)
- 의존성: 현재가 확인 (get_ticker_price)
- 위험도: 낮음 (높은 가격으로 체결 안됨, 취소 가능)
- Weight: 1
- 테스트: 
  - XRPUSDT, SELL, LIMIT
  - quantity=5
  - price = 현재가 * 1.5 (체결 안되게)
- 저장: 생성된 order_id

---

## Phase 7: Order Management - 주문 관리

### 7.1 get_order (새로 생성한 주문)
- 목적: 방금 생성한 LIMIT 주문 조회
- 의존성: Phase 6.1의 order_id
- 위험도: 없음 (읽기)
- Weight: 4
- 확인: status=NEW

### 7.2 get_open_orders
- 목적: 미체결 주문 목록에서 확인
- 의존성: Phase 6.1의 주문
- 위험도: 없음 (읽기)
- Weight: 6
- 확인: 방금 생성한 order_id 포함

### 7.3 cancel_order
- 목적: 주문 취소
- 의존성: Phase 6.1의 order_id
- 위험도: 중간 (주문 취소는 되돌릴 수 없음)
- Weight: 1
- 테스트: order_id로 취소
- 확인: 취소 응답

### 7.4 get_order (취소 확인)
- 목적: 취소된 주문 상태 확인
- 의존성: Phase 7.3
- 위험도: 없음 (읽기)
- Weight: 4
- 확인: status=CANCELED

---

## Phase 8: Advanced Orders - 복잡한 주문 (선택적)

### 8.1 create_oco_order
- 목적: OCO 주문 생성
- 의존성: 충분한 잔고
- 위험도: 높음 (실제 체결 가능)
- Weight: 1
- 테스트: 신중하게, 작은 수량으로
  - quantity=5
  - price = 현재가 * 1.3 (익절)
  - stopPrice = 현재가 * 0.7 (손절)

### 8.2 cancel_order_list
- 목적: OCO 주문 취소
- 의존성: Phase 8.1의 order_list_id
- 위험도: 중간
- Weight: 1

---

## 테스트하지 않을 메서드 (당분간)

- **get_historical_trades**: API 키 권한 필요 가능성
- **get_aggregate_trades**: 압축된 거래 내역 (get_recent_trades로 충분)
- **get_ui_klines**: UI용 캔들 (get_klines로 충분)
- **get_rolling_window_ticker**: 특수 케이스
- **create_oto_order, create_otoco_order**: 너무 복잡
- **create_sor_order, test_sor_order**: Smart Order Routing (특수 케이스)
- **cancel_open_orders**: 위험 (모든 주문 취소)
- **cancel_replace_order**: 복잡한 시나리오
- **get_all_order_list, get_open_order_list**: OCO 전용
- **get_my_allocations**: 할당 내역 (일반적으로 안씀)
- **get_rate_limit_order**: 레이트 리밋 확인 (필요시)
- **get_my_prevented_matches**: 특수 케이스
- **User Data Stream (3개)**: 웹소켓 연동 별도 작업

---

## 최종 테스트 순서 요약

1. **ping** ← 가장 먼저
2. **get_server_time**
3. **get_exchange_info** (XRPUSDT 정보)
4. **get_ticker_price**
5. **get_orderbook_ticker**
6. **get_order_book**
7. **get_klines**
8. **get_recent_trades**
9. **get_avg_price**
10. **get_my_trades** (방금 체결 확인)
11. **get_all_orders** (주문 내역)
12. **get_order** (과거 주문 ID로)
13. **get_open_orders**
14. **get_account_commission**
15. **test_order** (MARKET)
16. **test_order** (LIMIT)
17. **create_order** (LIMIT SELL, 높은 가격)
18. **get_order** (새 주문 확인)
19. **get_open_orders** (미체결 확인)
20. **cancel_order**
21. **get_order** (취소 확인)

**선택적:**
22. **create_oco_order**
23. **cancel_order_list**

---

## 예상 소요 시간

- Phase 1-5: 약 5분 (읽기 전용, 안전)
- Phase 6-7: 약 3분 (주문 생성/취소)
- Phase 8: 약 2분 (선택적)

**총 21개 메서드 테스트 예정**
