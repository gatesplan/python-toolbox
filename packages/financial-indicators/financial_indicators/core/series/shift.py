import numpy as np


def shift(arr: np.ndarray, periods: int = 1, fill_value: float = np.nan) -> np.ndarray:
    """
    배열 이동(Shift).

    배열을 앞뒤로 이동.

    Args:
        arr: 입력 데이터 배열
        periods: 이동 기간 (양수: 뒤로, 음수: 앞으로)
        fill_value: 빈 공간을 채울 값 (기본값: NaN)

    Returns:
        np.ndarray: 이동된 배열, 입력과 동일한 길이

    Examples:
        >>> arr = np.array([1, 2, 3, 4, 5])
        >>> shift(arr, periods=2)
        array([nan, nan,  1.,  2.,  3.])
        >>> shift(arr, periods=-1)
        array([ 2.,  3.,  4.,  5., nan])
    """
    if len(arr) == 0:
        return np.array([])

    if periods == 0:
        return arr.copy()

    result = np.full(len(arr), fill_value, dtype=np.float64)

    if periods > 0:
        # 뒤로 이동
        if periods < len(arr):
            result[periods:] = arr[:-periods]
    else:
        # 앞으로 이동
        abs_periods = abs(periods)
        if abs_periods < len(arr):
            result[:-abs_periods] = arr[abs_periods:]

    return result
