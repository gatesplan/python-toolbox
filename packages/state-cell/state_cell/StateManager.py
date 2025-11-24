from typing import Any, Callable, List
from .StateCell import StateCell


class StateManager(StateCell):
    def __init__(self,
                 cell: StateCell,
                 states: List[Any] = None,
                 initial: Any = None):
        super().__init__()
        self._cell = cell
        self.states = states
        self._current_state = initial
        self._original_initial = initial
        self._listeners: List[Callable[[Any, Any], None]] = []

    def update(self, value: Any, **kwargs) -> Any:
        old_state = self._current_state

        # Cell 업데이트 (인덱스 반환)
        idx = self._cell.update(value, **kwargs)

        # 상태 매핑
        new_state = self.states[idx] if self.states is not None else idx
        self._current_state = new_state

        # 상태가 바뀌었을 때만 notify
        if old_state != new_state:
            self._notify_listeners(old_state, new_state)

        return new_state

    def get_state(self) -> Any:
        return self._current_state

    def reset(self) -> None:
        self._cell.reset()
        self._current_state = self._original_initial
        # notify 하지 않음

    def add_listener(self, listener: Callable[[Any, Any], None]) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Any, Any], None]) -> None:
        self._listeners.remove(listener)

    def _notify_listeners(self, old_state: Any, new_state: Any) -> None:
        for listener in self._listeners:
            listener(old_state, new_state)
