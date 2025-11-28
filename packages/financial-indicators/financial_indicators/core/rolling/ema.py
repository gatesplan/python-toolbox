import numpy as np


def ema(arr: np.ndarray, span: int) -> np.ndarray:
    """
    지수이동평균(Exponential Moving Average) 계산.

    순차 계산 구현.

    Args:
        arr: 입력 데이터 배열
        span: EMA 스팬 (기간)

    Returns:
        np.ndarray: EMA 결과, 입력과 동일한 길이

    Raises:
        ValueError: span < 1인 경우

    Examples:
        >>> prices = np.array([100, 102, 101, 103, 105])
        >>> ema(prices, span=5)
        array([100.  , 100.67, 100.78, 101.52, 102.68])
    """
    if span < 1:
        raise ValueError("span must be >= 1")

    if len(arr) == 0:
        return np.array([])

    alpha = 2.0 / (span + 1.0)
    result = np.zeros_like(arr, dtype=np.float64)
    result[0] = arr[0]

    for i in range(1, len(arr)):
        result[i] = alpha * arr[i] + (1 - alpha) * result[i-1]

    return result
