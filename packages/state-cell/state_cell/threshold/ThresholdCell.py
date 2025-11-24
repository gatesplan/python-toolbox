from typing import Any
from ..StateCell import StateCell


class ThresholdCell(StateCell):
    def __init__(self, *thresholds: float):
        super().__init__()

        if len(thresholds) < 1:
            raise ValueError("ThresholdCell requires at least 1 threshold")

        # 중복 검사
        if len(thresholds) != len(set(thresholds)):
            raise ValueError("Duplicate thresholds are not allowed")

        self.thresholds = sorted(thresholds)
        self._state: int | None = None

    def update(self, value: float, **kwargs) -> int:
        # 경계값이면 이전 상태 유지
        if self._state is not None and value in self.thresholds:
            return self._state

        # 상태 계산: threshold를 넘은 횟수
        state = 0
        for t in self.thresholds:
            if value > t:
                state += 1
            else:
                break

        self._state = state
        return self._state

    def get_state(self) -> int | None:
        return self._state

    def reset(self) -> None:
        self._state = None
