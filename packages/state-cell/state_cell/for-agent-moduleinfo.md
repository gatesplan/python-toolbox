# State-Cell Module Information

실시간 제어 로직을 위한 조건부 상태 관리 라이브러리

## StateCell

모든 Cell의 기본 추상 클래스. 공통 인터페이스를 정의한다.

_state: Any = None    # 현재 상태값

__init__()
    StateCell 초기화

update(value: Any, **kwargs) -> Any
    raise NotImplementedError
    새로운 값으로 상태를 업데이트하고 현재 상태 반환

get_state() -> Any
    현재 상태값 반환

reset() -> None
    상태를 초기값으로 리셋

## StateManager

StateCell을 감싸서 내부 상태(인덱스)를 커스텀 상태로 매핑하고, 상태 변경 시 Observer들에게 통지하는 Wrapper 클래스

_cell: StateCell                              # 실제 로직 수행 Cell
states: List[Any] | None                      # 상태 매핑 테이블
_current_state: Any                           # 현재 외부 노출 상태
_original_initial: Any                        # reset용 초기 상태
_listeners: List[Callable[[Any, Any], None]]  # 상태 변경 listener 목록

__init__(cell: StateCell, states: List[Any] = None, initial: Any = None)
    StateManager 초기화

update(value: Any, **kwargs) -> Any
    내부 Cell 업데이트 후 매핑된 상태 반환, 변경 시 notify

get_state() -> Any
    현재 외부 노출 상태 반환

reset() -> None
    Cell 리셋 및 초기 상태 복원

add_listener(listener: Callable[[Any, Any], None]) -> None
    상태 변경 listener 등록

remove_listener(listener: Callable[[Any, Any], None]) -> None
    listener 제거

## HysteresisCell

구간(Interval) 기반 히스테리시스 상태 전환 Cell. 각 상태별 유효 구간 정의, 현재 구간 벗어나 다른 구간 진입 시 상태 전환.

상세 설명: `hysteresis/for-agent-moduleinfo.md` 참조

## ThresholdCell

N개 threshold로 N+1개 연속 구간 자동 생성, 경계 넘을 때만 상태 전환. 경계값에서는 이전 상태 유지.

상세 설명: `threshold/for-agent-moduleinfo.md` 참조

---

## 사용 패턴

### 기본 Cell 직접 사용
```python
cell = HysteresisCell('[-inf, 80]', '[20, inf)')
state_idx = cell.update(50)  # 인덱스 반환 (0, 1, ...)
```

### StateManager로 감싸서 사용
```python
manager = StateManager(
    cell=HysteresisCell('[-inf, 80]', '[20, inf)'),
    states=['LOW', 'HIGH'],
    initial='LOW'
)
manager.add_listener(lambda old, new: print(f"{old} → {new}"))
state = manager.update(50)  # 'LOW' or 'HIGH' 반환
```
