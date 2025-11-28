import numpy as np


def std(arr: np.ndarray, window: int, ddof: int = 1) -> np.ndarray:
    """
    롤링 표준편차(Rolling Standard Deviation) 계산.

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기
        ddof: 자유도 보정 (기본값: 1, 표본 표준편차)

    Returns:
        np.ndarray: 표준편차 결과, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: window < 2인 경우 (표준편차 계산 불가)

    Examples:
        >>> arr = np.array([1, 2, 3, 4, 5])
        >>> std(arr, window=3)
    """
    if window < 2:
        raise ValueError("window must be >= 2 for standard deviation calculation")

    n = len(arr)
    if n == 0:
        return np.array([])

    result = np.full(n, np.nan, dtype=np.float64)

    for i in range(window - 1, n):
        start_idx = i - window + 1
        window_data = arr[start_idx:i+1]
        result[i] = np.std(window_data, ddof=ddof)

    return result
