# Architecture - Throttle Pipeline

## Pattern

**CPSCP (Controller-Plugin-Service-Core-Particles) Pattern**

```
Controller → Plugin (Optional) → Service → Core → Particles
```

단일 도메인(Rate Limiting) 전담 모듈로, 계층적 의존성 흐름과 명확한 책임 분리를 따릅니다.

## Overview

Throttle Pipeline은 범용 rate limit 관리를 위한 적응형 쓰로틀링 시스템이다. 거래소 API(Binance, Upbit 등)뿐만 아니라 모든 rate-limited API에 적용 가능하며, 429 Too Many Requests 에러를 예방하고, 다중 시간 윈도우 제한(초/분/시간/일)을 동시에 추적하며, 실행 중 학습을 통해 최적의 요청 속도를 동적으로 조절한다.

모든 정책 결정(임계값, 윈도우 구성, 파싱 전략)은 매개변수화되어 있어, 사용자는 환경에 맞게 자유롭게 커스터마이징할 수 있다. 기본값을 제공하되 하드코딩을 최소화하여 확장성과 재사용성을 극대화한다.

### Core Features

- **Adaptive Throttling**: 설정 가능한 임계값 기반 동적 safe interval 계산, 평균 사용량 학습
- **Multi-Window Management**: 사용자 정의 다중 시간 윈도우 동시 추적, 가장 타이트한 제약 자동 선택
- **Dual Window Support**: Fixed Window (UTC 정각 리셋), Sliding Window (첫 요청 기준)
- **Ratchet Mechanism**: 비순차 응답으로 인한 잘못된 쓰로틀 완화 방지
- **Response-Based Tracking**: API 응답 헤더 파싱으로 실시간 rate limit 상태 갱신
- **Zero Request Loss**: 요청 거부 대신 지연으로 429 에러 회피
- **Pluggable Architecture**: HeaderParser 전략 패턴으로 새로운 API 지원 용이

### Design Philosophy

**매개변수화 우선**

모든 정책 결정은 하드코딩하지 않고 설정으로 주입받는다. 임계값(throttle_threshold), 히스토리 크기(usage_history_size), 윈도우 구성(WindowConfig 리스트) 등 모든 값은 기본값을 제공하되 사용자가 환경에 맞게 변경할 수 있다. 거래소별 차이는 전략 패턴(HeaderParser)으로 격리하여 새로운 API 지원 시 핵심 로직 수정 없이 Parser만 추가한다.

**적응형 학습 우선**

API 엔드포인트마다 다른 weight를 사전 정의하는 대신, 실행 중 Response header를 분석하여 실제 소모량을 학습한다. Binance의 klines 엔드포인트는 limit 파라미터에 따라 weight가 1~5로 변동하지만, 이를 테이블로 관리하지 않고 응답의 `X-MBX-USED-WEIGHT` 헤더로 실제 소모량을 파악한다. 정책 변경 시에도 코드 수정 없이 자동 대응한다.

**임계값 전략**

각 시간 윈도우의 사용량이 설정된 임계값(기본 50%) 미만일 때는 쓰로틀을 적용하지 않고 자유롭게 실행한다. 임계값 도달 시점부터 남은 여유를 남은 시간에 분배하는 safe interval을 계산하여 적용한다. 단, 초단위 윈도우(설정 가능한 기준 이하)는 정밀 계산 대신 단순화한다. Fixed Window는 리셋 시점까지 대기하여 정렬을 유지하고, Sliding Window는 윈도우 절반 대기로 충분한 여유를 확보한다. 장기 윈도우(분/시간/일)에서는 평균 사용량을 참고하여 safe interval을 조정한다.

**Ratchet 메커니즘**

비동기 API 호출 환경에서 응답이 비순차적으로 도착할 수 있다. 요청 A, B를 순서대로 보냈으나 응답 B가 먼저 도착하는 경우, B의 "여유 많음" 정보로 쓰로틀을 잘못 완화할 수 있다. Ratchet 메커니즘은 쓰로틀이 타이트해진 시점의 타임스탬프를 기록하고, current safe interval만큼 시간이 경과하기 전까지 완화를 제한한다. "safe interval로 한 번 대기했으면 충분히 안정되었다"는 직관에 기반하여, 타이트해진 후 최소한 safe interval 동안은 보수적 자세를 유지한다.

**Fixed vs Sliding Window**

Fixed Window는 UTC 기준 정각(매일 00:00, 매분 XX:00 등)에 리셋된다. 리셋 시간을 클라이언트가 계산할 수 있어 "남은 시간까지 남은 횟수 분배" 전략이 유효하다. Sliding Window는 첫 요청 시점부터 고정 시간(60초 등) 동안 윈도우가 유지되며, 리셋 시간이 고정되지 않는다. 두 방식 모두 지원하되, WindowTracker에서 타입별 처리를 분기한다.

### Dependencies

```toml
[project]
dependencies = []  # 핵심 로직은 외부 의존성 없음

[project.optional-dependencies]
binance = ["binance-connector>=3.12.0"]
upbit = ["python-upbit-api>=1.9.1"]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]
```

**Notes:**
- 핵심 라이브러리는 외부 API 클라이언트에 의존하지 않음
- 거래소별 라이브러리는 optional dependencies로 분리
- 사용자는 필요한 거래소만 선택적으로 설치 가능

## CPSCP Layer Structure

### Dependency Flow
```
Particles (데이터 구조, 상수)
    ↑
Core (순수 알고리즘, 전략 패턴)
    ↑
Service (비즈니스 로직 조합)
    ↑
Plugin (전략 선택, 편의 팩토리) - Optional
    ↑
Controller (공개 API, 워크플로우 조율)
```

### High-Level Architecture

```mermaid
graph TB
    subgraph "User"
        User[financial-gateway<br/>또는 직접 사용]
    end

    subgraph "Controller Layer"
        TWrap[ThrottleWrapper<br/>Generic Controller]
        PThru[PassthroughWrapper<br/>No Throttle]
    end

    subgraph "Plugin Layer (Optional)"
        BPlug[BinanceWrapper<br/>Convenience Factory]
        UPlug[UpbitWrapper<br/>Convenience Factory]
    end

    subgraph "Service Layer"
        Calc[ThrottleCalculator<br/>Business Logic]
    end

    subgraph "Core Layer"
        WTrack[WindowTracker<br/>Window State]
        UTrack[UsageTracker<br/>Usage Pattern]
        Ratch[RatchetState<br/>Throttle State]
        HParser[HeaderParser<br/>Parsing Strategy]
    end

    subgraph "Particles Layer"
        TConfig[ThrottleConfig]
        WConfig[WindowConfig]
        RInfo[RateLimitInfo]
    end

    User --> TWrap
    User --> BPlug
    User --> UPlug
    User --> PThru

    BPlug --> TWrap
    UPlug --> TWrap

    TWrap --> Calc
    Calc --> WTrack
    Calc --> UTrack
    Calc --> Ratch
    Calc --> TConfig

    WTrack --> HParser
    WTrack --> WConfig
    WTrack --> RInfo

    HParser --> RInfo
```

## Component Responsibilities

### Controller Layer

**ThrottleWrapper** (Generic Controller)
- 공개 API 제공: `call(request)`, `get_rate_limit_info()`
- 워크플로우 조율: 요청 → 쓰로틀 계산 → sleep → API 호출 → 응답 파싱 → 상태 갱신
- 모든 의존성 주입받아 동작: api_client, ThrottleConfig, WindowConfig 리스트, HeaderParser
- Stateful: WindowTracker 리스트, UsageTracker, ThrottleCalculator 보유

**PassthroughWrapper**
- 시뮬레이션 환경용 Controller
- 쓰로틀링 미적용, 즉시 실행
- 동일한 인터페이스 제공으로 환경 전환 용이

### Plugin Layer (Optional)

**BinanceWrapper** (Convenience Factory)
- ThrottleWrapper를 내부적으로 사용
- Binance 기본 설정 자동 구성:
  - WindowConfig: REQUEST_WEIGHT(1분), ORDERS(10초, 1일)
  - HeaderParser: BinanceHeaderParser
  - api_client: binance-connector 클라이언트
- 사용자는 config, windows 커스터마이징 가능

**UpbitWrapper** (Convenience Factory)
- ThrottleWrapper를 내부적으로 사용
- Upbit 기본 설정 자동 구성:
  - WindowConfig: 그룹별(order, default) Sliding Window
  - HeaderParser: UpbitHeaderParser
  - api_client: python-upbit-api 클라이언트
- 사용자는 config, windows 커스터마이징 가능

### Service Layer

**ThrottleCalculator** (Business Logic)
- 비즈니스 로직: safe interval 계산, 병목 윈도우 판단
- Core 알고리즘 조합:
  - WindowTracker들로부터 usage_ratio 수집
  - UsageTracker로부터 평균 간격 조회
  - RatchetState로 완화 조건 검증
- 워크플로우:
  1. 각 WindowTracker에서 usage_ratio 조회
  2. config.throttle_threshold와 비교
  3. 초과 윈도우에 대해 safe interval 계산
  4. config.short_window_threshold 기준으로 단순화 적용
  5. 가장 긴 interval 선택 (가장 타이트한 제약)
  6. RatchetState로 완화 검증
- Stateless: 상태는 WindowTracker/UsageTracker/RatchetState에 위임

### Core Layer

**WindowTracker** (Pure Algorithm)
- 개별 시간 윈도우(1초, 1분, 1시간, 1일 등)의 상태 추적
- WindowConfig로 구성 주입
- Fixed Window: UTC 기준 리셋 시간 계산
- Sliding Window: 윈도우 전체 시간을 남은 시간으로 사용
- HeaderParser로부터 파싱된 RateLimitInfo로 상태 갱신
- usage_ratio 계산, 리셋 시간까지 남은 시간 계산
- Stateful: 현재 remaining, limit, reset_time 보유

**UsageTracker** (Pure Algorithm)
- ThrottleConfig 주입
- 최근 N개(config.usage_history_size) 요청 간격을 deque로 기록
- 충분한 샘플(config.min_usage_samples) 확보 전에는 평균 미제공
- 평균 간격으로 "현재 속도로 계속 요청 시 예상 요청 수" 산출
- Stateful: deque 보유

**RatchetState** (Pure Algorithm)
- 현재 쓰로틀 interval 저장
- Interval 증가(타이트해짐) 시 타임스탬프와 interval 기록
- Interval 감소(완화) 시도 시 조건 검증:
  - 타이트해진 시점으로부터 `current_safe_interval` 경과했는지 확인
  - 경과 안 했으면 완화 거부, 경과했으면 허용
- Stateful: current_interval, tightened_at, tightened_interval 보유

**HeaderParser** (Strategy Pattern)
- 추상 인터페이스: `parse(headers: dict) -> Dict[str, RateLimitInfo]`
- BinanceHeaderParser 구현:
  - `X-MBX-USED-WEIGHT-1M`, `X-MBX-ORDER-COUNT-10S` 등 파싱
  - REQUEST_WEIGHT, ORDERS 윈도우별 RateLimitInfo 반환
- UpbitHeaderParser 구현:
  - `Remaining-Req: group=default; min=598; sec=9` 형식 파싱
  - 그룹별 RateLimitInfo 반환
- Stateless: 순수 파싱 로직만

### Particles Layer

**ThrottleConfig** (Configuration Dataclass)
- 쓰로틀링 관련 설정 (기본값 제공)
- `throttle_threshold: float = 0.5` (임계값)
- `usage_history_size: int = 100` (평균 추적 큐 크기)
- `min_usage_samples: int = 10` (평균 계산 최소 샘플 수)
- `short_window_threshold: int = 10` (초단위 윈도우 판단 기준, 초)
- `__post_init__`에서 검증 로직 포함
- 불변 권장

**WindowConfig** (Configuration Dataclass)
- 윈도우 설정 정보
- `limit: int` (최대 요청 수)
- `interval_seconds: int` (윈도우 시간, 초)
- `window_type: str` ("fixed" / "sliding")
- 불변 권장

**RateLimitInfo** (Data Dataclass)
- Rate limit 상태 정보
- `remaining: int` (남은 요청 수)
- `limit: int` (최대 요청 수)
- `reset_time: datetime` (리셋 시간)
- `usage_ratio: float` (사용률, 0.0~1.0)
- 불변 권장

## Directory Structure

```
throttle_pipeline/
├── Architecture.md                     # CPSCP 패턴 설계 문서
├── controller/                         # Controller Layer
│   ├── ThrottleWrapper/
│   │   ├── ThrottleWrapper.py
│   │   └── for-agent-moduleinfo.md
│   ├── PassthroughWrapper/
│   │   ├── PassthroughWrapper.py
│   │   └── for-agent-moduleinfo.md
│   └── for-agent-moduleinfo.md
├── plugin/                             # Plugin Layer (하위 폴더 없음)
│   ├── binance_wrapper.py
│   ├── upbit_wrapper.py
│   └── for-agent-moduleinfo.md
├── service/                            # Service Layer
│   ├── ThrottleCalculator/
│   │   ├── ThrottleCalculator.py
│   │   └── for-agent-moduleinfo.md
│   └── for-agent-moduleinfo.md
├── core/                               # Core Layer
│   ├── WindowTracker/
│   │   ├── WindowTracker.py
│   │   └── for-agent-moduleinfo.md
│   ├── UsageTracker/
│   │   ├── UsageTracker.py
│   │   └── for-agent-moduleinfo.md
│   ├── RatchetState/
│   │   ├── RatchetState.py
│   │   └── for-agent-moduleinfo.md
│   ├── HeaderParser/
│   │   ├── HeaderParser.py            # Base + BinanceHeaderParser + UpbitHeaderParser
│   │   └── for-agent-moduleinfo.md
│   └── for-agent-moduleinfo.md
└── particles/                          # Particles Layer (하위 폴더 없음)
    ├── throttle_config.py
    ├── window_config.py
    ├── rate_limit_info.py
    └── for-agent-moduleinfo.md
```

## Data Flow

1. User가 Controller.call(request) 호출
2. Controller가 UsageTracker.record_request()로 요청 간격 기록
3. Controller가 Service(ThrottleCalculator).get_current_throttle() 호출
4. Service가 각 Core(WindowTracker)에서 usage_ratio 조회
5. Service가 config.throttle_threshold와 비교하여 쓰로틀 필요 판단
6. Service가 Core(UsageTracker)에서 평균 간격 조회
7. Service가 임계값 초과 윈도우에 대해 safe interval 계산
8. Service가 config.short_window_threshold 기준으로 단순화 여부 판단
9. Service가 가장 긴 interval 선택 (가장 타이트한 제약)
10. Service가 Core(RatchetState).update_throttle_if_needed() 호출
11. Core(RatchetState)가 완화 조건 검증 후 current_throttle 반환
12. Controller가 throttle_interval만큼 time.sleep()
13. Controller가 실제 API 호출 (api_client)
14. API 응답 수신 (response.headers에 rate limit 정보 포함)
15. Controller가 Core(HeaderParser).parse(response.headers) 호출
16. Core(HeaderParser)가 윈도우별 RateLimitInfo 반환
17. Controller가 각 Core(WindowTracker).update_from_info() 호출하여 상태 갱신
18. Controller가 response 반환

## Development Order and Status

[Concept Design | Designing | Developing | Testing | Done | Deprecated]

### Phase 1: Particles (데이터/상수만)
1. [ThrottleConfig] Concept Design
2. [WindowConfig] Concept Design
3. [RateLimitInfo] Concept Design

### Phase 2: Core (순수 알고리즘)
4. [HeaderParser + BinanceHeaderParser + UpbitHeaderParser] Concept Design
5. [UsageTracker] Concept Design
6. [RatchetState] Concept Design
7. [WindowTracker] Concept Design

### Phase 3: Service (비즈니스 로직)
8. [ThrottleCalculator] Concept Design

### Phase 4: Controller (워크플로우)
9. [ThrottleWrapper] Concept Design
10. [PassthroughWrapper] Concept Design

### Phase 5: Plugin (편의 팩토리)
11. [BinanceWrapper] Concept Design
12. [UpbitWrapper] Concept Design

## CPSCP Principles

### 계층 분리
- 상위 계층은 하위 계층만 의존
- 하위 계층은 상위 계층을 알지 못함
- 동일 계층 간 의존성 최소화

### 금지사항
- **계층 건너뛰기**: Controller가 Core 직접 접근 금지
- **역방향 의존성**: Core가 Service 참조 금지
- **계층 내 순환 의존**: Service1 ↔ Service2 금지
- **Particles의 로직**: 순수 데이터/상수만, 비즈니스 로직 금지
- **Core의 불필요한 상태**: 상태 최소화, 정적 메서드 권장

### Naming Convention
- Controller: ThrottleWrapper, PassthroughWrapper
- Plugin: BinanceWrapper, UpbitWrapper
- Service: ThrottleCalculator
- Core: WindowTracker, UsageTracker, RatchetState, HeaderParser
- Particles: ThrottleConfig, WindowConfig, RateLimitInfo
