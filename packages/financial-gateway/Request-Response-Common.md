# Request/Response 공통 구조

## 개요

모든 Request와 Response가 공유하는 공통 데이터 구조 및 원칙을 정의한다.

## Request 공통 구조

모든 Request 객체는 다음 필드를 포함한다:

**필수 필드:**
- `request_id`: 요청 추적 식별자 (문자열)
- `gateway_name`: 대상 Gateway 이름 ("binance", "upbit", "simulation")

**원칙:**
- 각 Request는 고유한 `request_id`를 가진다
- `request_id`는 내부에서 자동 생성하거나 외부에서 주입 가능
- 주문 생성 시 `request_id`를 `order_id`로 요청할 수 있음 (거래소 지원 여부에 따라)

## Response 공통 구조

모든 Response 객체는 다음 필드를 포함한다:

**필수 필드:**
- `request_id`: 원본 요청 참조 (문자열)
- `is_success`: 성공/실패 구분 (불린)

**시간 정보 (UTC 밀리세컨드 timestamp):**
- `send_when`: from user - 요청 전송 시각
- `receive_when`: from user - 응답 수신 시각
- `processed_when`: from server - 서버 처리 시각 (없으면 `(send_when + receive_when) / 2`)
- `timegaps`: `receive_when - send_when` (밀리세컨드)

**실패 정보 (`is_success=false`일 때만):**
- `error_code`: 에러 코드 (평소 None)
- `error_message`: 에러 메시지 (평소 None)

**시간 처리 원칙:**
- 모든 시간은 UTC 표준시 기준
- 밀리세컨드 단위 timestamp
- `send_when`, `receive_when`은 클라이언트(user) 시간
- `processed_when`은 서버 시간 (우선), 없으면 중간값으로 자동 계산
- 시간대 차이는 시스템 동기화 문제이며, Gateway 관심사가 아님

## Request 목록

오토트레이딩을 위한 필수 Request 12개:

**주문 생명주기:**
1. `create_order` - 주문 생성
2. `cancel_order` - 주문 취소
3. `modify_or_replace_order` - 주문 수정/교체

**조회 - 시장:**
4. `see_orderbook` - 호가창 조회
5. `see_ticker` - 현재 시세 조회
6. `see_candles` - 캔들 데이터 조회
7. `see_available_markets` - 거래 가능 마켓 목록

**조회 - 계정:**
8. `see_balance` - 내 자산 조회
9. `see_order` - 특정 주문 상태 조회
10. `see_open_orders` - 활성 주문 목록 조회
11. `see_trades` - 체결 내역 조회

**조회 - 시스템:**
12. `see_server_time` - 서버 시간 조회

## 설계 철학

**"see" 동사 선택**
- 조회 Request는 "see" 동사 사용
- get, fetch, check, query 대신 "see" 선택
- 이유: 간결하고 직관적이며 사용자 친화적

**독립 개발 원칙**
- 각 Request/Response는 독립적으로 설계 및 구현
- 그룹핑하지 않음
- 각 Request마다 별도의 상세 설계 필요

**Gateway 책임 범위**
- Gateway는 Request를 받아 Response를 반환하는 진입점
- 성공/실패 여부만 판단, 재시도나 우선순위는 외부 책임
- 시간 정보 기록 및 에러 정보 전달이 주 책임

**create_order의 포괄성**
- 모든 주문 타입을 하나의 `create_order`로 처리
- `side`, `order_type`, `time_in_force` 등 파라미터로 구분
- 이전 설계(타입별 분리)보다 사용자 진입점 단순화

## 다음 단계

각 Request/Response의 구체적 파라미터 및 결과 구조는 개별 문서에서 정의:
- `create_order` 상세 설계
- `cancel_order` 상세 설계
- `see_orderbook` 상세 설계
- ... (각 Request별)

**구체 설계 시 수행 사항:**
- 거래소 API 조사
- 필수/선택 파라미터 정의
- Response 성공 시 데이터 구조
- Response 실패 시 에러 케이스 및 코드 정의
