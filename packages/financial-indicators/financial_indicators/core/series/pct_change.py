import numpy as np


def pct_change(arr: np.ndarray, periods: int = 1) -> np.ndarray:
    """
    퍼센트 변화율(Percent Change) 계산.

    Args:
        arr: 입력 데이터 배열
        periods: 비교 기간 (기본값: 1)

    Returns:
        np.ndarray: 퍼센트 변화율 배열, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: periods < 1인 경우

    Examples:
        >>> arr = np.array([100, 102, 101, 103])
        >>> pct_change(arr, periods=1)
        array([nan, 0.02, -0.0098..., 0.0198...])
    """
    if periods < 1:
        raise ValueError("periods must be >= 1")

    if len(arr) == 0:
        return np.array([])

    result = np.full(len(arr), np.nan, dtype=np.float64)

    for i in range(periods, len(arr)):
        prev_val = arr[i - periods]
        if prev_val == 0:
            result[i] = np.nan
        else:
            result[i] = (arr[i] - prev_val) / prev_val

    return result
