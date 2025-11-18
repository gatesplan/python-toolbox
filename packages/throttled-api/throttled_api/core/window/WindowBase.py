"""
Window strategy base class
"""
from abc import ABC, abstractmethod
from typing import Optional


class WindowBase(ABC):
    """
    Window 전략의 추상 베이스 클래스

    모든 Window 구현체는 remaining 값으로 남은 용량을 차감식으로 관리한다.
    """

    def __init__(self, limit: int, window_seconds: int, max_soft_delay: float = 0.5):
        """
        Args:
            limit: 윈도우 내 최대 허용량
            window_seconds: 윈도우 시간 (초)
            max_soft_delay: soft limiting 최대 대기 시간 (초), 기본 0.5초
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_soft_delay = max_soft_delay
        self.remaining = limit

    @abstractmethod
    def can_send(self, cost: int) -> bool:
        """
        지금 보낼 수 있는지 판단

        Args:
            cost: 요청 소모량

        Returns:
            True if remaining >= cost
        """
        pass

    @abstractmethod
    def consume(self, cost: int) -> float:
        """
        사용량 차감

        Args:
            cost: 요청 소모량

        Returns:
            차감 시점의 timestamp
        """
        pass

    @abstractmethod
    def refund(self, timestamp: float, cost: int) -> None:
        """
        요청 실패 시 소모량 환불

        Args:
            timestamp: 차감했던 시점
            cost: 환불할 소모량
        """
        pass

    @abstractmethod
    def wait_time(self, cost: int = 0) -> float:
        """
        다시 시도 가능할 때까지 대기 시간 (초)

        Soft rate limiting: 남은 용량을 남은 시간 동안 균등 분배
        - delay = cost × (time_left / remaining)
        - max_soft_delay 초과 시 경고 로깅 및 cap

        Hard rate limiting: remaining < cost 시 리셋/만료까지 대기

        Args:
            cost: 요청할 소모량 (0이면 현재 상태만 체크)

        Returns:
            대기 시간 (초), 즉시 가능하면 0
        """
        pass

    def get_remaining_rate(self) -> float:
        """
        남은 용량 비율

        Returns:
            0.0 ~ 1.0
        """
        return self.remaining / self.limit if self.limit > 0 else 0.0
