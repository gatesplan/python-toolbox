# throttled_api.core.window

Window 전략 모듈 - API 사용량 윈도우 관리 전략

## WindowBase

Window 전략의 추상 베이스 클래스. 모든 Window 전략이 구현해야 할 인터페이스 정의.

```
limit: int              # 윈도우 내 최대 허용량
window_seconds: int     # 윈도우 시간 범위 (초)
remaining: int          # 현재 남은 용량 (차감식 관리)

can_send(cost: int) -> bool
    cost만큼 소비 가능한지 판단 (remaining >= cost)

consume(cost: int) -> float
    raise ValueError  # cost > remaining 시
    cost만큼 용량 차감하고 현재 timestamp 반환

refund(timestamp: float, cost: int) -> None
    요청 실패 시 소비량 환불. timestamp로 특정 소비 항목 식별.

wait_time() -> float
    다시 시도 가능할 때까지 대기 시간(초) 반환. 즉시 가능하면 0.

get_remaining_rate() -> float
    남은 용량 비율 (0.0 ~ 1.0) 반환. remaining / limit 계산.
```

## FixedWindow

고정 윈도우 전략 - 특정 시점에 전체 용량 리셋

```
next_reset_time: float  # 다음 리셋 시각 (timestamp)

can_send(cost: int) -> bool
    리셋 체크 후 remaining >= cost 판단

consume(cost: int) -> float
    raise ValueError  # cost > remaining 시
    리셋 체크 후 remaining -= cost, 현재 timestamp 반환

refund(timestamp: float, cost: int) -> None
    remaining += cost (timestamp 무시, 즉시 환불)

wait_time() -> float
    remaining < cost 시 next_reset_time까지 남은 시간 반환
```

**특징**:
- 윈도우 만료 시점에 전체 용량이 한번에 리셋
- 개별 소비 항목의 히스토리를 추적하지 않음
- refund 시 timestamp를 무시하고 즉시 remaining 증가

## SlidingWindow

슬라이딩 윈도우 전략 - 개별 소비 항목이 시간 경과 후 회복

```
history: Deque[Tuple[float, int]]  # (timestamp, cost) 큐

can_send(cost: int) -> bool
    만료 항목 제거 후 remaining >= cost 판단

consume(cost: int) -> float
    raise ValueError  # cost > remaining 시
    만료 항목 제거 후 (now, cost)를 history에 추가, remaining -= cost

refund(timestamp: float, cost: int) -> None
    history를 역순 탐색하여 (timestamp ± 0.001, cost) 매칭 항목 제거
    매칭 시 remaining += cost

wait_time() -> float
    remaining < cost 시 가장 오래된 항목의 만료 시각까지 남은 시간 반환
```

**특징**:
- 각 소비 항목이 window_seconds 경과 후 개별적으로 회복
- history에 (timestamp, cost) 큐로 소비 내역 추적
- refund 시 역순 검색으로 timestamp와 cost가 모두 일치하는 항목 제거
- 만료 항목 제거 시 remaining이 자동 회복
