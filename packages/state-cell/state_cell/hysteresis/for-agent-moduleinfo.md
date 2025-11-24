# HysteresisCell

구간(Interval) 기반 히스테리시스 상태 전환 Cell. 각 상태별로 유효 구간을 정의하고, 현재 상태의 구간을 벗어나 다른 구간에 진입할 때만 상태를 전환한다.

intervals: List[Interval]  # 각 상태의 유효 구간 (portion.Interval)
_state: int | None         # 현재 상태 인덱스 (0, 1, 2, ..., 초기값 None)

## 초기화

__init__(*interval_specs: Union[str, Interval]) -> None
    HysteresisCell 초기화

    Args:
        *interval_specs: 구간 정의 (최소 2개)
            - 문자열: '[0, 50]', '(20, 80]', '[-inf, 100)' 등
            - Interval: P.closed(0, 50), P.openclosed(20, 80) 등

    Raises:
        ValueError: interval_specs가 2개 미만일 경우

    Notes:
        - N개 구간 → N개 상태 (인덱스 0 ~ N-1)
        - 문자열은 P.from_string(s, conv=float)로 파싱
        - 초기 상태는 None (첫 update() 호출 시 결정)

## 상태 업데이트

update(value: float, **kwargs) -> int
    값을 입력받아 상태를 업데이트하고 현재 상태 인덱스 반환

    Args:
        value: 입력 값 (숫자)
        **kwargs: 사용하지 않음 (인터페이스 일관성)

    Returns:
        int: 현재 상태 인덱스 (0, 1, 2, ...)

    Raises:
        ValueError: value가 어느 구간에도 속하지 않을 경우 (미결정)

    동작 로직:
        1. 첫 호출 (상태 None): value가 속한 구간 찾아서 초기 상태 설정
        2. 상태 확정 후:
            - value가 현재 상태 구간에 포함 → 상태 유지
            - value가 현재 상태 구간을 벗어남 → 다른 구간 찾기
                - 다른 구간 j에 포함 → 상태 j로 전환
                - 어느 구간에도 없음 → ValueError (미결정)

    Notes:
        - 히스테리시스 효과: 구간이 겹치는 영역에서 상태 유지
        - 현재 상태 구간을 벗어나야만 다른 상태로 전환 가능

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
import portion as P
from state_cell.hysteresis import HysteresisCell

# 예시 1: 2-상태 히스테리시스 (문자열)
cell = HysteresisCell('[-inf, 80]', '[20, inf)')
# 상태 0: (-∞, 80]
# 상태 1: [20, +∞)
# 히스테리시스 영역: [20, 80]

cell.update(30)  # 0 (초기 상태)
cell.update(50)  # 0 (여전히 구간 0 안)
cell.update(85)  # 1 (구간 0 벗어남, 구간 1 진입)
cell.update(70)  # 1 (히스테리시스 영역, 상태 유지)
cell.update(15)  # 0 (구간 1 벗어남, 구간 0 진입)

# 예시 2: Interval 객체 사용
cell = HysteresisCell(
    P.closedopen(0, 80),
    P.closed(20, 100)
)

# 예시 3: 3-상태 히스테리시스
cell = HysteresisCell(
    '[-inf, 20]',   # COLD 구간
    '[15, 30]',     # NORMAL 구간
    '[25, inf)'     # HOT 구간
)

cell.update(10)  # 0 (COLD)
cell.update(18)  # 1 (NORMAL, 겹침 영역 진입)
cell.update(28)  # 2 (HOT, 겹침 영역 진입)
cell.update(22)  # 2 (HOT, 여전히 구간 안)

# 예시 4: StateManager와 조합
from state_cell import StateManager

manager = StateManager(
    cell=HysteresisCell('[-inf, 80]', '[20, inf)'),
    states=['LOW', 'HIGH'],
    initial='LOW'
)

manager.add_listener(lambda old, new: print(f"{old} → {new}"))
manager.update(85)  # 출력: "LOW → HIGH"
```

**의존성:**
- `portion>=2.5.0`: 수학적 구간 표현 및 포함 검사

**미결정 사항:**
1. value가 어느 구간에도 속하지 않을 때 처리 방법
2. value가 여러 구간에 동시 속할 때 우선순위 규칙
