import pandas as pd


class TickToTimestampWorker:
    """틱 단위를 타임스탬프로 역변환"""

    def __call__(self, ticks: pd.Series, unit: int) -> pd.Series:
        """
        틱 Series를 타임스탬프 Series로 변환

        Args:
            ticks: 틱 단위로 저장된 시간 데이터
            unit: 틱 변환 단위

        Returns:
            타임스탬프 Series
        """
        return ticks * unit
