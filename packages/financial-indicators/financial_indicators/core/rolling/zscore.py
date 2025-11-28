import numpy as np
from .sma import sma as sma_func
from .std import std as std_func


def zscore(arr: np.ndarray, window: int, ddof: int = 1) -> np.ndarray:
    """
    롤링 Z-Score 계산.

    SMA와 STD를 조합하여 표준화 점수 계산.

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기
        ddof: 자유도 보정 (기본값: 1)

    Returns:
        np.ndarray: Z-Score 결과, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: window < 2인 경우

    Examples:
        >>> arr = np.array([1, 2, 3, 4, 5])
        >>> zscore(arr, window=3)
    """
    if window < 2:
        raise ValueError("window must be >= 2 for zscore calculation")

    if len(arr) == 0:
        return np.array([])

    # SMA와 STD 계산
    mean = sma_func(arr, window)
    std = std_func(arr, window, ddof=ddof)

    # Z-Score 계산 (0 나누기 방지)
    result = np.where(std > 0, (arr - mean) / std, 0)

    # std가 NaN인 위치는 결과도 NaN
    result = np.where(np.isnan(std), np.nan, result)

    return result
