import numpy as np


def standardize(arr: np.ndarray, mean: float | None = None, std: float | None = None) -> np.ndarray:
    """
    표준화(Z-Score Normalization).

    평균을 빼고 표준편차로 나눔.

    Args:
        arr: 입력 데이터 배열
        mean: 사용할 평균값 (None이면 arr의 평균 사용)
        std: 사용할 표준편차 (None이면 arr의 표준편차 사용)

    Returns:
        np.ndarray: 표준화된 배열, 입력과 동일한 길이

    Examples:
        >>> arr = np.array([1, 2, 3, 4, 5])
        >>> standardize(arr)
        # 평균 0, 표준편차 1로 변환
    """
    if len(arr) == 0:
        return np.array([])

    if mean is None:
        mean = np.mean(arr)

    if std is None:
        std = np.std(arr, ddof=1)

    # std가 0인 경우 모든 값을 0으로 설정
    if std == 0:
        return np.zeros_like(arr, dtype=np.float64)

    return ((arr - mean) / std).astype(np.float64)
