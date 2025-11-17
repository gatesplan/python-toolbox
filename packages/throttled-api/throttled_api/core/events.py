"""
Throttle event classes
"""
from dataclasses import dataclass


@dataclass
class ThrottleEvent:
    """
    쓰로틀 이벤트

    Pipeline이 임계값 하회 시 발행하는 노티피케이션
    """

    timeframe: str  # 예: "1m", "1h", "1d"
    remaining_rate: float  # 0.0 ~ 1.0
    remaining_cap: int  # 남은 용량 (절대값)

    def __repr__(self):
        return (
            f"ThrottleEvent(timeframe={self.timeframe}, "
            f"remaining_rate={self.remaining_rate:.2f}, "
            f"remaining_cap={self.remaining_cap})"
        )
