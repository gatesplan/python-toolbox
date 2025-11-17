# throttled_api.core

쓰로틀링 코어 모듈 - 다중 타임프레임 API 요청 제한 관리

## events

쓰로틀 이벤트 정의 모듈

### ThrottleEvent

Pipeline이 임계값 하회 시 발행하는 이벤트

```
timeframe: str          # 타임프레임 이름 (예: "1m", "1h", "1d")
remaining_rate: float   # 남은 용량 비율 (0.0 ~ 1.0)
remaining_cap: int      # 남은 용량 절대값
```

## Pipeline

단일 타임프레임 제약 관리 + 이벤트 발행

```
timeframe: str                              # 타임프레임 이름
window: WindowBase                          # Window 전략 객체
threshold: Optional[float]                  # 이벤트 발행 임계값 (0.0 ~ 1.0)
_listeners: List[Callable]                  # 이벤트 리스너 목록
_below_threshold: bool                      # 연속 발행 방지 플래그

can_send(cost: int) -> bool
    Window에 위임. 통과 시 _below_threshold 플래그 리셋.

consume(cost: int) -> float
    Window에 위임 후 임계값 체크 및 이벤트 발행

refund(timestamp: float, cost: int) -> None
    Window에 위임 후 임계값 위로 회복 시 플래그 리셋

wait_time() -> float
    Window에 위임

add_listener(listener: Callable[[ThrottleEvent], None]) -> None
    이벤트 리스너 등록

remove_listener(listener: Callable[[ThrottleEvent], None]) -> None
    이벤트 리스너 제거
```

**이벤트 발행 조건**:
- threshold가 None이 아니고
- remaining_rate < threshold이고
- _below_threshold가 False일 때 (연속 발행 방지)

**이벤트 발행 후**:
- _below_threshold = True로 설정
- 등록된 모든 리스너에게 ThrottleEvent 전달

## BaseThrottler

여러 Pipeline 조율 + 옵저버 패턴 Subject

```
pipelines: List[Pipeline]                   # Pipeline 리스트
_lock: asyncio.Lock                         # 동시성 제어용 Lock
_event_listeners: List[Callable]            # 외부 이벤트 리스너

async _check_and_wait(cost: int) -> None
    모든 Pipeline이 통과할 때까지 대기 후 소비

add_event_listener(listener: Callable[[ThrottleEvent], None]) -> None
    외부 이벤트 리스너 등록

remove_event_listener(listener: Callable[[ThrottleEvent], None]) -> None
    외부 이벤트 리스너 제거
```

**_check_and_wait 동작**:
1. Lock 획득
2. 모든 Pipeline의 can_send(cost) 체크
3. 모두 통과 시 모든 Pipeline에 consume(cost) 후 반환
4. 하나라도 실패 시 각 Pipeline의 wait_time() 중 최댓값만큼 대기 후 재시도

**이벤트 전파**:
- 각 Pipeline의 이벤트를 _on_pipeline_event로 수신
- 수신한 이벤트를 모든 외부 리스너에게 전파

**동시성 제어**:
- asyncio.Lock으로 동시 요청 직렬화
- 경쟁 조건 방지 및 정확한 용량 관리 보장

## window/

Window 전략 모듈. 자세한 내용은 `window/for-agent-moduleinfo.md` 참조.

- WindowBase: Window 전략 추상 베이스 클래스
- FixedWindow: 고정 윈도우 전략 (리셋 기반)
- SlidingWindow: 슬라이딩 윈도우 전략 (개별 회복)
