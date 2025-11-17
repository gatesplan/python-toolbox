"""
Fixed Window strategy implementation
"""
import time
from .WindowBase import WindowBase


class FixedWindow(WindowBase):
    """
    Fixed Window 전략

    특정 시점에 전체 용량이 리셋되는 방식.
    단일 카운터(remaining)로 관리하며, 리셋 시각 도달 시 remaining = limit으로 회복.
    """

    def __init__(self, limit: int, window_seconds: int):
        """
        Args:
            limit: 윈도우 내 최대 허용량
            window_seconds: 윈도우 시간 (초)
        """
        super().__init__(limit, window_seconds)
        self.next_reset_time = time.time() + window_seconds

    def _check_and_reset(self) -> None:
        """
        현재 시각 확인하여 리셋 시각 도달 시 리셋
        """
        now = time.time()
        if now >= self.next_reset_time:
            self.remaining = self.limit
            # 다음 리셋 시각 계산 (누적 오차 방지)
            self.next_reset_time = now + self.window_seconds

    def can_send(self, cost: int) -> bool:
        """
        지금 보낼 수 있는지 판단

        Args:
            cost: 요청 소모량

        Returns:
            True if remaining >= cost
        """
        self._check_and_reset()
        return self.remaining >= cost

    def consume(self, cost: int) -> float:
        """
        사용량 차감

        Args:
            cost: 요청 소모량

        Returns:
            차감 시점의 timestamp
        """
        self._check_and_reset()
        self.remaining -= cost
        return time.time()

    def refund(self, timestamp: float, cost: int) -> None:
        """
        요청 실패 시 소모량 환불

        FixedWindow는 timestamp를 무시하고 단순히 remaining += cost

        Args:
            timestamp: 차감했던 시점 (무시됨)
            cost: 환불할 소모량
        """
        self.remaining += cost

    def wait_time(self, cost: int = 0) -> float:
        """
        다시 시도 가능할 때까지 대기 시간 (초)

        Soft rate limiting: 50% 이상 소진 시 점진적 딜레이
        Hard rate limiting: 용량 부족 시 다음 리셋까지 대기

        Args:
            cost: 요청할 소모량

        Returns:
            대기 시간 (초), 즉시 가능하면 0
        """
        self._check_and_reset()

        # Hard limit 1: 이미 over-consumed 상태 (remaining < 0)
        if self.remaining <= 0:
            now = time.time()
            wait = self.next_reset_time - now
            return max(0.0, wait)

        # Hard limit 2: 요청한 cost가 부족
        if cost > 0 and self.remaining < cost:
            now = time.time()
            wait = self.next_reset_time - now
            return max(0.0, wait)

        # Soft limit: 50% 이상 소진 시 점진적 딜레이
        remaining_rate = self.get_remaining_rate()
        if remaining_rate >= 0.5:
            return 0.0

        # 점진적 딜레이: remaining_rate가 0.5 → 0으로 갈수록 증가
        # normalized: 0 (50% 남음) → 1 (0% 남음)
        normalized = (0.5 - remaining_rate) / 0.5
        max_delay = 1.0  # 최대 1초
        return normalized * max_delay
