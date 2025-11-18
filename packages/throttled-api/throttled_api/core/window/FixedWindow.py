"""
Fixed Window strategy implementation
"""
import time
import logging
from .WindowBase import WindowBase


logger = logging.getLogger(__name__)


class FixedWindow(WindowBase):
    """
    Fixed Window 전략

    특정 시점에 전체 용량이 리셋되는 방식.
    단일 카운터(remaining)로 관리하며, 리셋 시각 도달 시 remaining = limit으로 회복.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        max_soft_delay: float = 0.5,
        threshold: float = 0.5,
    ):
        """
        Args:
            limit: 윈도우 내 최대 허용량
            window_seconds: 윈도우 시간 (초)
            max_soft_delay: soft limiting 최대 대기 시간 (초), 기본 0.5초
            threshold: soft limiting 시작 임계값 (0.0 ~ 1.0), 기본 0.5
        """
        super().__init__(limit, window_seconds, max_soft_delay, threshold)
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

        Soft rate limiting: threshold 미만일 때 균등 분배 방식으로 delay
        Hard rate limiting: 용량 부족 시 다음 리셋까지 대기

        Args:
            cost: 요청할 소모량

        Returns:
            대기 시간 (초), 즉시 가능하면 0
        """
        self._check_and_reset()

        # Hard limit 1: 이미 over-consumed 상태
        if self.remaining <= 0:
            return max(0.0, self.next_reset_time - time.time())

        # Hard limit 2: 요청한 cost가 부족
        if cost > 0 and self.remaining < cost:
            return max(0.0, self.next_reset_time - time.time())

        # cost가 0이면 대기 없음
        if cost == 0:
            return 0.0

        # Soft limit: threshold 이상이면 즉시 허용
        remaining_rate = self.get_remaining_rate()
        if self.threshold is not None and remaining_rate >= self.threshold:
            return 0.0  # 즉시 허용

        # threshold 미만이면 균등 분배 방식으로 soft delay 적용
        time_until_reset = max(0.0, self.next_reset_time - time.time())

        if self.remaining > 0:
            # delay_per_unit = 리셋까지 남은 시간 / 남은 용량
            delay_per_unit = time_until_reset / self.remaining
            calculated_delay = cost * delay_per_unit

            # max_soft_delay 초과 시 경고 및 cap
            if calculated_delay > self.max_soft_delay:
                logger.warning(
                    f"[Soft Limit Exceeded] calculated_delay={calculated_delay:.3f}s > "
                    f"max={self.max_soft_delay}s, cost={cost}, "
                    f"remaining={self.remaining}/{self.limit} "
                    f"({remaining_rate:.0%}), "
                    f"time_left={time_until_reset:.1f}s "
                    f"(Consider reducing request rate)"
                )
                return self.max_soft_delay

            return calculated_delay

        return 0.0
