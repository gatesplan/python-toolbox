import numpy as np


def log_return(arr: np.ndarray, periods: int = 1) -> np.ndarray:
    """
    로그 수익률(Log Return) 계산.

    Args:
        arr: 입력 데이터 배열
        periods: 비교 기간 (기본값: 1)

    Returns:
        np.ndarray: 로그 수익률 배열, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: periods < 1인 경우
        ValueError: arr에 0 이하 값이 있는 경우 (로그 불가)

    Examples:
        >>> arr = np.array([100, 102, 101, 103])
        >>> log_return(arr, periods=1)
    """
    if periods < 1:
        raise ValueError("periods must be >= 1")

    if len(arr) == 0:
        return np.array([])

    if np.any(arr <= 0):
        raise ValueError("All values must be > 0 for log return calculation")

    result = np.full(len(arr), np.nan, dtype=np.float64)

    for i in range(periods, len(arr)):
        result[i] = np.log(arr[i] / arr[i - periods])

    return result
