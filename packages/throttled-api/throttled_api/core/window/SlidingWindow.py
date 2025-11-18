"""
Sliding Window strategy implementation
"""
import time
import logging
from collections import deque
from typing import Deque, Tuple
from .WindowBase import WindowBase


logger = logging.getLogger(__name__)


class SlidingWindow(WindowBase):
    """
    Sliding Window 전략

    개별 사용 시점부터 정확히 N 시간 후 회복하는 방식.
    remaining 값과 (timestamp, cost) 히스토리 큐를 함께 관리.
    """

    def __init__(self, limit: int, window_seconds: int, max_soft_delay: float = 0.5):
        """
        Args:
            limit: 윈도우 내 최대 허용량
            window_seconds: 윈도우 시간 (초)
            max_soft_delay: soft limiting 최대 대기 시간 (초), 기본 0.5초
        """
        super().__init__(limit, window_seconds, max_soft_delay)
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

        Soft rate limiting: 남은 용량을 다음 회복까지 균등 분배
        Hard rate limiting: 용량 부족 시 가장 오래된 항목 만료까지 대기

        Args:
            cost: 요청할 소모량

        Returns:
            대기 시간 (초), 즉시 가능하면 0
        """
        self._remove_expired()

        # Hard limit: over-consumed 또는 cost 부족
        if self.remaining <= 0 or (cost > 0 and self.remaining < cost):
            if not self.history:
                return 0.0

            # 가장 오래된 항목이 만료되는 시간
            oldest_timestamp, _ = self.history[0]
            expiration_time = oldest_timestamp + self.window_seconds
            return max(0.0, expiration_time - time.time())

        # cost가 0이면 대기 없음
        if cost == 0:
            return 0.0

        # Soft limit: 균등 분배 방식
        if self.history:
            # 가장 오래된 항목이 만료될 때까지 남은 시간
            oldest_timestamp, _ = self.history[0]
            time_until_recovery = max(0.0,
                (oldest_timestamp + self.window_seconds) - time.time()
            )

            if self.remaining > 0:
                # delay_per_unit = 다음 회복까지 시간 / 남은 용량
                delay_per_unit = time_until_recovery / self.remaining
                calculated_delay = cost * delay_per_unit

                # max_soft_delay 초과 시 경고 및 cap
                if calculated_delay > self.max_soft_delay:
                    logger.warning(
                        f"[Soft Limit Exceeded] calculated_delay={calculated_delay:.3f}s > "
                        f"max={self.max_soft_delay}s, cost={cost}, "
                        f"remaining={self.remaining}/{self.limit} "
                        f"({self.get_remaining_rate():.0%}), "
                        f"next_recovery={time_until_recovery:.1f}s "
                        f"(Consider reducing request rate)"
                    )
                    return self.max_soft_delay

                return calculated_delay

        return 0.0
