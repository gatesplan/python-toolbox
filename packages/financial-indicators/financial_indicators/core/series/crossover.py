import numpy as np


def crossover(arr: np.ndarray, reference: np.ndarray | float) -> np.ndarray:
    """
    교차(Crossover) 탐지.

    배열이 기준선을 교차하는 지점 탐지.

    Args:
        arr: 입력 데이터 배열
        reference: 기준선 (배열 또는 스칼라)

    Returns:
        np.ndarray: 교차 신호 배열 (1: 상향 교차, -1: 하향 교차, 0: 교차 없음)

    Raises:
        ValueError: reference가 배열이면서 arr와 길이가 다른 경우

    Examples:
        >>> arr = np.array([1, 2, 3, 2, 1])
        >>> reference = 2.0
        >>> crossover(arr, reference)
        array([0,  1,  0, -1,  0])
    """
    if len(arr) == 0:
        return np.array([])

    # reference를 배열로 변환
    if isinstance(reference, (int, float)):
        ref = np.full_like(arr, reference, dtype=np.float64)
    else:
        ref = np.asarray(reference, dtype=np.float64)
        if len(ref) != len(arr):
            raise ValueError("reference length must match arr length")

    result = np.zeros(len(arr), dtype=np.int32)

    for i in range(1, len(arr)):
        prev_above = arr[i-1] > ref[i-1]
        curr_above = arr[i] > ref[i]

        if not prev_above and curr_above:
            # 상향 교차 (Golden Cross)
            result[i] = 1
        elif prev_above and not curr_above:
            # 하향 교차 (Death Cross)
            result[i] = -1

    return result
