# see_server_time Request/Response 설계

## 개요

서버 시간 조회 요청. 거래소 서버와 로컬 시스템 간 시간 동기화 확인 및 타임스탬프 기준 수립을 위해 사용한다.

## see_server_time Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 추가 필드
없음. 서버 시간 조회는 파라미터가 필요 없다.

## see_server_time Response 구조

### 공통 필드 (Response Base)
- `request_id`: 원본 요청 참조
- `is_success`: 성공/실패
- `send_when`: UTC ms
- `receive_when`: UTC ms
- `processed_when`: UTC ms (서버 처리 시각)
- `timegaps`: ms
- `error_code`: 에러 코드 (실패 시)
- `error_message`: 에러 메시지 (실패 시)

### 성공 시 응답 데이터

**서버 시간:**
- `server_time: int` - 서버 시간 (UTC ms)

**참고:**
- BaseResponse의 `processed_when` 필드와 `server_time` 필드는 동일한 값을 가질 수 있음
- 하지만 명시적으로 `server_time`을 별도 필드로 제공하여 사용자 편의성 제공

### 실패 시 에러 코드

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

**참고:** 서버 시간 조회는 실패율이 매우 낮음. 대부분의 경우 성공한다.

## 설계 원칙

### 3단계 Fallback 전략

Gateway 구현 시 다음 우선순위로 서버 시간을 획득한다:

**1단계: 서버 타임 전용 API 사용**
- 거래소가 서버 시간 조회 전용 API를 제공하면 우선 사용
- 예: Binance `GET /api/v3/time`, Upbit `GET /v1/status/server_time`

**2단계: 타임스탬프 포함 API 사용**
- 서버 타임 전용 API가 없으면, 타임스탬프를 포함하는 API 중 선택
- 선택 조건:
  - 가벼운 API (응답 크기 작음, 처리 빠름)
  - 사이드이펙트 없음 (조회만 수행, 상태 변경 없음)
  - 인증 불필요 (공개 API 우선)
- 예: 마켓 정보 조회, 시세 조회 등

**3단계: 로컬 타임 사용**
- 위 두 가지가 모두 불가능한 경우 로컬 시스템 시간 사용
- `server_time = int(time.time() * 1000)`
- 응답은 성공으로 처리하되, 로그에 fallback 사용 기록

### 시간 동기화 검증

**사용자 활용 방법:**
```python
response = gateway.execute(SeeServerTimeRequest(...))
local_time = response.receive_when
server_time = response.server_time
time_diff = abs(server_time - local_time)

if time_diff > 1000:  # 1초 이상 차이
    logger.warning(f"로컬과 서버 시간 차이: {time_diff}ms")
```

**주의사항:**
- 네트워크 지연으로 인해 수십~수백ms 차이는 정상
- 수초 이상 차이는 시스템 시간 동기화 문제 가능성

### 인증 불필요

대부분의 거래소는 서버 시간 조회에 API 키 인증을 요구하지 않는다. Gateway 구현 시 공개 엔드포인트 우선 사용한다.
