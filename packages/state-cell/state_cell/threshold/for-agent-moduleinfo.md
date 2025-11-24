# ThresholdCell

N개 threshold로 N+1개 연속 구간을 자동 생성하고, 경계를 넘을 때만 상태를 전환하는 Cell. 경계값에서는 이전 상태를 유지하여 안정적인 상태 관리를 제공한다.

thresholds: List[float]  # 정렬된 threshold 목록
_state: int | None       # 현재 상태 인덱스 (0, 1, 2, ..., 초기값 None)

## 초기화

__init__(*thresholds: float) -> None
    ThresholdCell 초기화

    Args:
        *thresholds: threshold 값들 (최소 1개)

    Raises:
        ValueError: threshold가 0개일 경우
        ValueError: 중복된 threshold가 있을 경우

    Notes:
        - N개 threshold → N+1개 상태
        - 자동 정렬됨
        - 초기 상태는 None (첫 update() 호출 시 결정)

## 구간 생성 규칙

N개 threshold [t0, t1, t2, ..., t(N-1)]로 N+1개 연속 구간 생성:

```
상태 0: ~ t0
상태 1: t0 ~ t1
상태 2: t1 ~ t2
...
상태 i: t(i-1) ~ ti
...
상태 N: t(N-1) ~
```

## 상태 업데이트

update(value: float, **kwargs) -> int
    값을 입력받아 상태를 업데이트하고 현재 상태 인덱스 반환

    Args:
        value: 입력 값 (숫자)
        **kwargs: 사용하지 않음 (인터페이스 일관성)

    Returns:
        int: 현재 상태 인덱스 (0, 1, 2, ...)

    동작 로직:
        1. 경계값이면 이전 상태 유지
        2. 아니면 threshold를 넘은 횟수로 상태 결정

    Notes:
        - 경계값(threshold와 정확히 같은 값): 이전 상태 유지
        - 경계를 넘어야만 상태 전환 발생

## 상태 조회

get_state() -> int | None
    현재 상태 인덱스 반환

    Returns:
        int | None: 현재 상태 인덱스 (초기화 전이면 None)

## 초기화

reset() -> None
    상태를 None으로 리셋 (다음 update()에서 재초기화)

---

**사용 예시:**

```python
from state_cell.threshold import ThresholdCell

# 예시 1: 단일 threshold (2-상태)
cell = ThresholdCell(50)

cell.update(40)  # 0 (~ 50)
cell.update(50)  # 0 (경계값, 이전 유지)
cell.update(51)  # 1 (50 ~, 경계 넘음!)
cell.update(50)  # 1 (경계값, 이전 유지)
cell.update(49)  # 0 (경계 넘음!)

# 예시 2: 다중 threshold (3-상태)
cell = ThresholdCell(50, 80)

cell.update(30)  # 0 (~ 50)
cell.update(60)  # 1 (50 ~ 80)
cell.update(90)  # 2 (80 ~)
cell.update(70)  # 1 (80 밑으로)
cell.update(40)  # 0 (50 밑으로)

# 예시 3: 자동 정렬
cell = ThresholdCell(80, 20, 50)  # 내부적으로 [20, 50, 80]로 정렬

cell.update(10)  # 0 (~ 20)
cell.update(30)  # 1 (20 ~ 50)
cell.update(60)  # 2 (50 ~ 80)
cell.update(90)  # 3 (80 ~)

# 예시 4: 경계값 동작
cell = ThresholdCell(50, 60, 100)

cell.update(40)  # 0
cell.update(50)  # 0 (경계값, 0 유지)
cell.update(51)  # 1 (50 경계 넘음)
cell.update(50)  # 1 (경계값, 1 유지)
cell.update(49)  # 0 (50 경계 넘음)

# 예시 5: StateManager와 조합
from state_cell import StateManager

manager = StateManager(
    cell=ThresholdCell(20, 50, 80),
    states=['COLD', 'COOL', 'WARM', 'HOT'],
    initial='COLD'
)

manager.add_listener(lambda old, new: print(f"{old} → {new}"))

manager.update(10)  # 'COLD'
manager.update(30)  # 'COOL' (출력: COLD → COOL)
manager.update(60)  # 'WARM' (출력: COOL → WARM)
manager.update(90)  # 'HOT' (출력: WARM → HOT)
```

**HysteresisCell과의 차이:**

- **ThresholdCell**: threshold로 연속 구간 자동 생성, 겹침 없음
- **HysteresisCell**: 구간 직접 지정, 겹침 허용 (히스테리시스 효과)

```python
# ThresholdCell: 편리함
ThresholdCell(10, 20, 30)  # 자동 구간 생성

# HysteresisCell: 정확함
HysteresisCell(
    '(-inf, 20]',
    '[10, 30]',
    '[20, inf)'
)  # 구간 직접 지정, 겹침 가능
```

**의존성:** 없음 (순수 Python)
