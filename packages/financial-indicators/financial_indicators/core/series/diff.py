import numpy as np


def diff(arr: np.ndarray, periods: int = 1) -> np.ndarray:
    """
    차분(Difference) 계산.

    현재 값에서 이전 값을 뺌.

    Args:
        arr: 입력 데이터 배열
        periods: 차분 기간 (기본값: 1)

    Returns:
        np.ndarray: 차분 배열, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: periods < 1인 경우

    Examples:
        >>> arr = np.array([100, 102, 101, 103, 105])
        >>> diff(arr, periods=1)
        array([nan,  2., -1.,  2.,  2.])
    """
    if periods < 1:
        raise ValueError("periods must be >= 1")

    if len(arr) == 0:
        return np.array([])

    result = np.full(len(arr), np.nan, dtype=np.float64)

    for i in range(periods, len(arr)):
        result[i] = arr[i] - arr[i - periods]

    return result
