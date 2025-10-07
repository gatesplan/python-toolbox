import pandas as pd
from functools import reduce
from math import gcd


class TimestampToTickWorker:
    """타임스탬프를 틱 단위로 변환하여 저장용량 절감"""

    def __call__(self, timestamps: pd.Series) -> tuple[pd.Series, int]:
        """
        타임스탬프 Series를 틱 Series와 unit으로 변환

        변환 로직:
        1. timestamp의 diff 계산
        2. unique 값만 추출
        3. 최대공약수를 계산하여 unit으로 사용
        4. timestamp 전체를 unit으로 나눈 몫을 tick으로 변환

        Args:
            timestamps: 타임스탬프 Series

        Returns:
            (ticks: pd.Series, unit: int)
        """
        # 단일 행인 경우 unit=1
        if len(timestamps) == 1:
            unit = 1
            ticks = timestamps.astype(int)
            return ticks, unit

        # diff 계산 (첫 값은 NaN이므로 제외)
        diffs = timestamps.diff().dropna()

        # unique 값만 추출
        unique_diffs = diffs.unique()

        # 최대공약수 계산
        unit = reduce(gcd, unique_diffs.astype(int))

        # timestamp를 unit으로 나눈 몫을 tick으로 변환
        ticks = (timestamps // unit).astype(int)

        return ticks, unit
