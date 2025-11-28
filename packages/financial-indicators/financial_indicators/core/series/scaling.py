import numpy as np


def scaling(arr: np.ndarray, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray:
    """
    Min-Max 스케일링.

    배열을 지정된 범위로 정규화.

    Args:
        arr: 입력 데이터 배열
        min_val: 스케일링 최솟값 (기본값: 0.0)
        max_val: 스케일링 최댓값 (기본값: 1.0)

    Returns:
        np.ndarray: 스케일링된 배열, 입력과 동일한 길이

    Raises:
        ValueError: min_val >= max_val인 경우

    Examples:
        >>> arr = np.array([1, 2, 3, 4, 5])
        >>> scaling(arr, min_val=0.0, max_val=1.0)
        array([0.  , 0.25, 0.5 , 0.75, 1.  ])
    """
    if min_val >= max_val:
        raise ValueError("min_val must be < max_val")

    if len(arr) == 0:
        return np.array([])

    arr_min = np.min(arr)
    arr_max = np.max(arr)

    # arr.max() == arr.min()인 경우 모든 값을 min_val로 설정
    if arr_max == arr_min:
        return np.full_like(arr, min_val, dtype=np.float64)

    # Min-Max 스케일링
    normalized = (arr - arr_min) / (arr_max - arr_min)
    scaled = normalized * (max_val - min_val) + min_val

    return scaled.astype(np.float64)
