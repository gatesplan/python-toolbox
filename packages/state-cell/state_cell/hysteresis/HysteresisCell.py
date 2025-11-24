from typing import Union, List, Any
import portion as P
from portion import Interval
from ..StateCell import StateCell
from .UnboundedValueError import UnboundedValueError


class HysteresisCell(StateCell):
    def __init__(self,
                 *interval_specs: Union[str, Interval],
                 error_on_outside: bool = False):
        super().__init__()

        if len(interval_specs) < 2:
            raise ValueError("HysteresisCell requires at least 2 intervals")

        self.intervals: List[Interval] = [
            self._parse_interval(spec) for spec in interval_specs
        ]
        self.error_on_outside = error_on_outside
        self._state: int | None = None

    def update(self, value: float, **kwargs) -> int:
        # 첫 호출: 초기 상태 결정
        if self._state is None:
            idx = self._find_containing_interval(value)
            if idx is None:
                if self.error_on_outside:
                    raise UnboundedValueError(
                        f"Value {value} is outside all defined intervals"
                    )
                # 첫 호출인데 어느 구간에도 없으면 상태 0으로 시작
                self._state = 0
            else:
                self._state = idx
            return self._state

        # 현재 상태 구간에 포함되는지 확인
        if value in self.intervals[self._state]:
            # 상태 유지
            return self._state

        # 현재 상태 구간을 벗어남 - 다른 구간 찾기
        new_idx = self._find_containing_interval(value)

        if new_idx is None:
            # 어느 구간에도 속하지 않음
            if self.error_on_outside:
                raise UnboundedValueError(
                    f"Value {value} is outside all defined intervals"
                )
            # 상태 유지
            return self._state

        # 상태 전환
        self._state = new_idx
        return self._state

    def get_state(self) -> int | None:
        return self._state

    def reset(self) -> None:
        self._state = None

    def _parse_interval(self, spec: Union[str, Interval]) -> Interval:
        # 문자열 또는 Interval 객체를 Interval로 변환
        if isinstance(spec, str):
            return P.from_string(spec, conv=float)
        return spec

    def _find_containing_interval(self, value: float) -> int | None:
        # value가 속한 구간의 인덱스 찾기
        # 여러 구간에 속하면 첫 번째 구간 반환
        for idx, interval in enumerate(self.intervals):
            if value in interval:
                return idx
        return None
