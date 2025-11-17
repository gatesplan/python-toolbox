"""
Pipeline implementation
"""
from typing import List, Callable, Optional
from .window.WindowBase import WindowBase
from .events import ThrottleEvent


class Pipeline:
    """
    단일 타임프레임 제약 관리 + 이벤트 발행

    Window 전략을 내부에서 사용하며, can_send/consume/refund/wait_time을 Window에 위임.
    독자적 책임은 사용률 모니터링과 이벤트 발행.
    """

    def __init__(
        self,
        timeframe: str,
        window: WindowBase,
        threshold: Optional[float] = None,
    ):
        """
        Args:
            timeframe: 타임프레임 이름 (예: "1m", "1h", "1d")
            window: Window 전략 객체
            threshold: 이벤트 발행 임계값 (0.0 ~ 1.0), None이면 이벤트 발행 안 함
        """
        self.timeframe = timeframe
        self.window = window
        self.threshold = threshold
        self._listeners: List[Callable[[ThrottleEvent], None]] = []
        self._below_threshold = False  # 연속 발행 방지

    def can_send(self, cost: int) -> bool:
        """
        지금 보낼 수 있는지 판단 (Window에 위임)

        Args:
            cost: 요청 소모량

        Returns:
            True if remaining >= cost
        """
        result = self.window.can_send(cost)

        # can_send가 True면 회복된 것이므로 플래그 리셋
        if result and self._below_threshold:
            self._below_threshold = False

        return result

    def consume(self, cost: int) -> float:
        """
        사용량 차감 (Window에 위임) 및 이벤트 발행

        Args:
            cost: 요청 소모량

        Returns:
            차감 시점의 timestamp
        """
        timestamp = self.window.consume(cost)

        # 임계값 체크 및 이벤트 발행
        self._check_and_emit_event()

        return timestamp

    def refund(self, timestamp: float, cost: int) -> None:
        """
        요청 실패 시 소모량 환불 (Window에 위임)

        Args:
            timestamp: 차감했던 시점
            cost: 환불할 소모량
        """
        self.window.refund(timestamp, cost)

        # 환불 후 임계값 위로 회복되었는지 체크
        if self.threshold is not None:
            remaining_rate = self.window.get_remaining_rate()
            if remaining_rate >= self.threshold:
                self._below_threshold = False

    def wait_time(self, cost: int = 0) -> float:
        """
        다시 시도 가능할 때까지 대기 시간 (Window에 위임)

        Args:
            cost: 요청할 소모량

        Returns:
            대기 시간 (초), 즉시 가능하면 0
        """
        return self.window.wait_time(cost)

    def add_listener(self, listener: Callable[[ThrottleEvent], None]) -> None:
        """
        이벤트 리스너 등록

        Args:
            listener: ThrottleEvent를 받는 콜백 함수
        """
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[ThrottleEvent], None]) -> None:
        """
        이벤트 리스너 제거

        Args:
            listener: 제거할 콜백 함수
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _check_and_emit_event(self) -> None:
        """
        임계값 체크 및 이벤트 발행
        """
        if self.threshold is None:
            return

        remaining_rate = self.window.get_remaining_rate()

        # 임계값 하회 시 이벤트 발행 (연속 발행 방지)
        if remaining_rate < self.threshold and not self._below_threshold:
            self._below_threshold = True
            event = ThrottleEvent(
                timeframe=self.timeframe,
                remaining_rate=remaining_rate,
                remaining_cap=self.window.remaining,
            )
            self._emit_event(event)

    def _emit_event(self, event: ThrottleEvent) -> None:
        """
        등록된 모든 리스너에게 이벤트 전달

        Args:
            event: 발행할 이벤트
        """
        for listener in self._listeners:
            listener(event)
