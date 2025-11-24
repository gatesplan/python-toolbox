from abc import ABC, abstractmethod
from typing import Any


class StateCell(ABC):
    def __init__(self):
        self._state: Any = None

    @abstractmethod
    def update(self, value: Any, **kwargs) -> Any:
        # 새로운 값으로 상태 업데이트하고 현재 상태 반환
        pass

    def get_state(self) -> Any:
        # 현재 상태 반환
        return self._state

    def reset(self) -> None:
        # 상태를 초기값으로 리셋
        self._state = None
