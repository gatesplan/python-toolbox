import numpy as np


def max(arr: np.ndarray, window: int) -> np.ndarray:
    """
    롤링 최댓값(Rolling Maximum) 계산.

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기

    Returns:
        np.ndarray: 롤링 최댓값 결과, 입력과 동일한 길이

    Raises:
        ValueError: window < 1인 경우

    Examples:
        >>> arr = np.array([1, 3, 2, 5, 4])
        >>> max(arr, window=3)
        array([1., 3., 3., 5., 5.])
    """
    if window < 1:
        raise ValueError("window must be >= 1")

    n = len(arr)
    if n == 0:
        return np.array([])

    result = np.zeros(n, dtype=np.float64)

    for i in range(n):
        start_idx = max(0, i - window + 1)
        result[i] = np.max(arr[start_idx:i+1])

    return result
