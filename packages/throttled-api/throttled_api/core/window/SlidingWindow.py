"""
Sliding Window strategy implementation
"""
import time
from collections import deque
from typing import Deque, Tuple
from .WindowBase import WindowBase


class SlidingWindow(WindowBase):
    """
    Sliding Window 전략

    개별 사용 시점부터 정확히 N 시간 후 회복하는 방식.
    remaining 값과 (timestamp, cost) 히스토리 큐를 함께 관리.
    """

    def __init__(self, limit: int, window_seconds: int):
        """
        Args:
            limit: 윈도우 내 최대 허용량
            window_seconds: 윈도우 시간 (초)
        """
        super().__init__(limit, window_seconds)
        self.history: Deque[Tuple[float, int]] = deque()

    def _remove_expired(self) -> None:
        """
        만료된 항목을 히스토리에서 제거하고 remaining 회복
        """
        now = time.time()
        cutoff = now - self.window_seconds

        while self.history and self.history[0][0] < cutoff:
            _, cost = self.history.popleft()
            self.remaining += cost

    def can_send(self, cost: int) -> bool:
        """
        지금 보낼 수 있는지 판단

        Args:
            cost: 요청 소모량

        Returns:
            True if remaining >= cost
        """
        self._remove_expired()
        return self.remaining >= cost

    def consume(self, cost: int) -> float:
        """
        사용량 차감

        Args:
            cost: 요청 소모량

        Returns:
            차감 시점의 timestamp
        """
        self._remove_expired()
        now = time.time()
        self.history.append((now, cost))
        self.remaining -= cost
        return now

    def refund(self, timestamp: float, cost: int) -> None:
        """
        요청 실패 시 소모량 환불

        큐를 역순으로 순회하며 동일한 timestamp와 cost를 가진 첫 번째 항목 찾아 제거

        Args:
            timestamp: 차감했던 시점
            cost: 환불할 소모량
        """
        # 역순으로 검색 (deque는 reversed 사용)
        for i, (ts, c) in enumerate(reversed(self.history)):
            if abs(ts - timestamp) < 0.001 and c == cost:  # timestamp는 부동소수점이므로 근사 비교
                # 역순 인덱스를 정순 인덱스로 변환
                actual_index = len(self.history) - 1 - i
                del self.history[actual_index]
                self.remaining += cost
                return

    def wait_time(self, cost: int = 0) -> float:
        """
        다시 시도 가능할 때까지 대기 시간 (초)

        Soft rate limiting: 50% 이상 소진 시 점진적 딜레이
        Hard rate limiting: 용량 부족 시 가장 오래된 항목 만료까지 대기

        Args:
            cost: 요청할 소모량

        Returns:
            대기 시간 (초), 즉시 가능하면 0
        """
        self._remove_expired()

        # Hard limit 1: 이미 over-consumed 상태 또는 요청한 cost가 부족
        if self.remaining <= 0 or (cost > 0 and self.remaining < cost):
            if not self.history:
                return 0.0

            # 가장 오래된 항목이 만료되는 시간
            oldest_timestamp, _ = self.history[0]
            expiration_time = oldest_timestamp + self.window_seconds
            now = time.time()
            wait = expiration_time - now
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
