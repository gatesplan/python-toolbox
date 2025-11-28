import numpy as np


def sma(arr: np.ndarray, window: int) -> np.ndarray:
    """
    단순이동평균(Simple Moving Average) 계산.

    NumPy convolution 기반 고속 연산.

    Args:
        arr: 입력 데이터 배열
        window: 이동평균 윈도우 크기

    Returns:
        np.ndarray: SMA 결과, 입력과 동일한 길이 (초기값 cumulative mean으로 패딩)

    Raises:
        ValueError: window < 1인 경우

    Examples:
        >>> prices = np.array([100, 102, 101, 103, 105])
        >>> sma(prices, window=3)
        array([100. , 101. , 101. , 102. , 103. ])
    """
    if window < 1:
        raise ValueError("window must be >= 1")

    n = len(arr)

    # 빈 배열 처리
    if n == 0:
        return np.array([])

    # window >= n인 경우: cumulative mean 반환
    if window >= n:
        return np.cumsum(arr) / np.arange(1, n + 1)

    # window == 1인 경우: 원본 배열 반환
    if window == 1:
        return arr.copy()

    # 일반 케이스: convolution 사용
    kernel = np.ones(window) / window
    full_conv = np.convolve(arr, kernel, mode='valid')

    # 초기 window-1개 값은 cumulative mean으로 패딩
    prefix = np.cumsum(arr[:window-1]) / np.arange(1, window)

    return np.concatenate([prefix, full_conv])
