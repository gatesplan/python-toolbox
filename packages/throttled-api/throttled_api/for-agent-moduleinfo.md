# throttled_api

API 요청 제한 관리 패키지 - 다중 타임프레임 쓰로틀링 프레임워크

## 개요

throttled_api는 API 요청 제한(rate limit)을 관리하는 프레임워크입니다.
여러 타임프레임(1초당, 1분당, 1시간당 등)의 제약을 동시에 처리하며,
Fixed Window와 Sliding Window 전략을 지원합니다.

## 핵심 개념

**차감식 용량 관리**:
- 남은 용량(remaining)을 기준으로 관리
- consume() 시 remaining -= cost
- 만료/리셋 시 remaining 회복

**다중 타임프레임 제약**:
- 여러 Pipeline(예: 1초당 10개, 1분당 100개)을 동시 관리
- 모든 Pipeline이 통과해야만 요청 허용
- 하나라도 차단 시 자동 대기

**Window 전략**:
- FixedWindow: 특정 시점에 전체 용량 리셋
- SlidingWindow: 개별 소비 항목이 시간 경과 후 회복

**이벤트 발행**:
- Pipeline이 임계값 하회 시 ThrottleEvent 발행
- 옵저버 패턴으로 외부 리스너에게 전파
- 로깅, 알림 등에 활용

## 구조

```
throttled_api/
├── core/                   # 코어 프레임워크
│   ├── window/            # Window 전략
│   │   ├── WindowBase     # 추상 베이스
│   │   ├── FixedWindow    # 고정 윈도우
│   │   └── SlidingWindow  # 슬라이딩 윈도우
│   ├── events             # 이벤트 클래스
│   ├── Pipeline           # 단일 타임프레임 관리
│   └── BaseThrottler      # 다중 Pipeline 조율
└── providers/             # API별 구체 구현 (미구현)
    ├── binance/
    └── upbit/
```

## core/

코어 프레임워크 모듈. 자세한 내용은 `core/for-agent-moduleinfo.md` 참조.

**주요 컴포넌트**:
- window.WindowBase: Window 전략 인터페이스
- window.FixedWindow: 고정 윈도우 구현
- window.SlidingWindow: 슬라이딩 윈도우 구현
- events.ThrottleEvent: 임계값 하회 이벤트
- Pipeline: 단일 타임프레임 제약 + 이벤트 발행
- BaseThrottler: 다중 Pipeline 조율 + asyncio 기반 자동 대기

## providers/

API별 구체 구현 모듈 (아직 미구현)

**계획된 Provider**:
- binance: Binance API 쓰로틀러
- upbit: Upbit API 쓰로틀러

각 Provider는 BaseThrottler를 상속하여 API별 Pipeline 구성 및
엔드포인트별 cost 계산 로직을 구현합니다.

## 사용 예시

### 기본 사용

```python
from throttled_api.core.window import FixedWindow, SlidingWindow
from throttled_api.core.Pipeline import Pipeline
from throttled_api.core.BaseThrottler import BaseThrottler

# Pipeline 생성
p1 = Pipeline("1s", FixedWindow(limit=10, window_seconds=1))
p2 = Pipeline("1m", SlidingWindow(limit=100, window_seconds=60))

# Throttler 생성
throttler = BaseThrottler(pipelines=[p1, p2])

# 요청 전 체크 (자동 대기)
await throttler._check_and_wait(cost=1)
# API 요청 실행
response = await api_client.request()
```

### 이벤트 리스너

```python
def on_threshold_event(event):
    print(f"[WARNING] {event.timeframe} usage: {event.remaining_rate:.1%}")

# Pipeline에 임계값 설정 및 리스너 등록
p1 = Pipeline("1m", FixedWindow(100, 60), threshold=0.2)
throttler = BaseThrottler(pipelines=[p1])
throttler.add_event_listener(on_threshold_event)

# 사용률 80% 초과 시 이벤트 발행
await throttler._check_and_wait(81)
# 출력: [WARNING] 1m usage: 19.0%
```

### 환불 메커니즘

```python
# 요청 전 소비
timestamps = {}
for pipeline in throttler.pipelines:
    timestamps[pipeline.timeframe] = pipeline.consume(cost=5)

try:
    response = await api_client.request()
except Exception:
    # 요청 실패 시 환불
    for pipeline in throttler.pipelines:
        pipeline.refund(timestamps[pipeline.timeframe], cost=5)
```

## 설계 원칙

1. **단순성**: 큐/워커 없이 asyncio 기반 자동 대기로 간결한 구조
2. **확장성**: WindowBase 추상화로 새로운 전략 추가 가능
3. **타입 안정성**: 타입 힌트 사용으로 명확한 인터페이스
4. **테스트 가능성**: TDD로 개발, 69개 테스트 커버리지
5. **제로 의존성**: 코어는 표준 라이브러리만 사용 (asyncio, time, collections)
