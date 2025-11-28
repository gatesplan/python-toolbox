import numpy as np


def wma(arr: np.ndarray, window: int) -> np.ndarray:
    """
    가중이동평균(Weighted Moving Average) 계산.

    선형 가중치 적용 (최근 값에 더 높은 가중치).

    Args:
        arr: 입력 데이터 배열
        window: 가중 이동평균 윈도우 크기

    Returns:
        np.ndarray: WMA 결과, 입력과 동일한 길이

    Raises:
        ValueError: window < 1인 경우

    Examples:
        >>> prices = np.array([1, 2, 3, 4, 5])
        >>> wma(prices, window=3)
        # 가중치: [1, 2, 3]
    """
    if window < 1:
        raise ValueError("window must be >= 1")

    n = len(arr)
    if n == 0:
        return np.array([])

    result = np.zeros(n)
    weights = np.arange(1, window + 1, dtype=np.float64)
    weights_sum = weights.sum()

    for i in range(n):
        start_idx = max(0, i - window + 1)
        end_idx = i + 1
        current_window_size = end_idx - start_idx

        if current_window_size <= window:
            current_weights = weights[-current_window_size:]
            current_weights_sum = current_weights.sum()

            window_data = arr[start_idx:end_idx]
            result[i] = np.dot(window_data, current_weights) / current_weights_sum
        else:
            window_data = arr[start_idx:end_idx]
            result[i] = np.dot(window_data, weights) / weights_sum

    return result
