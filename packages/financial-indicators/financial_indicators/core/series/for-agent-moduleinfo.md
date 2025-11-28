# scaling
Min-Max 스케일링. 배열을 지정된 범위로 정규화.

scaling(arr: np.ndarray, min_val: float = 0.0, max_val: float = 1.0) -> np.ndarray
    배열을 [min_val, max_val] 범위로 스케일링

    Args:
        arr: 입력 데이터 배열
        min_val: 스케일링 최솟값 (기본값: 0.0)
        max_val: 스케일링 최댓값 (기본값: 1.0)

    Returns:
        np.ndarray: 스케일링된 배열, 입력과 동일한 길이

    Raises:
        ValueError: min_val >= max_val인 경우

    Notes:
        - 공식: (arr - arr.min()) / (arr.max() - arr.min()) * (max_val - min_val) + min_val
        - arr.max() == arr.min()인 경우 모든 값을 min_val로 설정
        - 원본 배열은 수정되지 않음

# standardize
표준화(Z-Score Normalization). 평균을 빼고 표준편차로 나눔.

standardize(arr: np.ndarray, mean: float | None = None, std: float | None = None) -> np.ndarray
    배열을 표준화 (평균 0, 표준편차 1)

    Args:
        arr: 입력 데이터 배열
        mean: 사용할 평균값 (None이면 arr의 평균 사용)
        std: 사용할 표준편차 (None이면 arr의 표준편차 사용)

    Returns:
        np.ndarray: 표준화된 배열, 입력과 동일한 길이

    Notes:
        - 공식: (arr - mean) / std
        - std가 0인 경우 모든 값을 0으로 설정 (0 나누기 방지)
        - mean, std를 명시하면 외부 통계값으로 표준화 가능

# pct_change
퍼센트 변화율(Percent Change) 계산.

pct_change(arr: np.ndarray, periods: int = 1) -> np.ndarray
    배열의 퍼센트 변화율 계산

    Args:
        arr: 입력 데이터 배열
        periods: 비교 기간 (기본값: 1)

    Returns:
        np.ndarray: 퍼센트 변화율 배열, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: periods < 1인 경우

    Notes:
        - 공식: (arr[i] - arr[i-periods]) / arr[i-periods]
        - 초기 periods개 값은 NaN
        - arr[i-periods]가 0인 경우 해당 위치는 NaN

# log_return
로그 수익률(Log Return) 계산.

log_return(arr: np.ndarray, periods: int = 1) -> np.ndarray
    배열의 로그 수익률 계산

    Args:
        arr: 입력 데이터 배열
        periods: 비교 기간 (기본값: 1)

    Returns:
        np.ndarray: 로그 수익률 배열, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: periods < 1인 경우
        ValueError: arr에 0 이하 값이 있는 경우 (로그 불가)

    Notes:
        - 공식: log(arr[i] / arr[i-periods]) = log(arr[i]) - log(arr[i-periods])
        - 초기 periods개 값은 NaN
        - 연속 복리 수익률 계산에 사용

# diff
차분(Difference) 계산. 현재 값에서 이전 값을 뺌.

diff(arr: np.ndarray, periods: int = 1) -> np.ndarray
    배열의 차분 계산

    Args:
        arr: 입력 데이터 배열
        periods: 차분 기간 (기본값: 1)

    Returns:
        np.ndarray: 차분 배열, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: periods < 1인 경우

    Notes:
        - 공식: arr[i] - arr[i-periods]
        - 초기 periods개 값은 NaN
        - 시계열 데이터의 정상성(Stationarity) 확보에 사용

# crossover
교차(Crossover) 탐지. 배열이 기준선을 교차하는 지점 탐지.

crossover(arr: np.ndarray, reference: np.ndarray | float) -> np.ndarray
    배열이 기준선을 교차하는 지점 탐지

    Args:
        arr: 입력 데이터 배열
        reference: 기준선 (배열 또는 스칼라)

    Returns:
        np.ndarray: 교차 신호 배열 (1: 상향 교차, -1: 하향 교차, 0: 교차 없음)

    Raises:
        ValueError: reference가 배열이면서 arr와 길이가 다른 경우

    Notes:
        - 상향 교차(Golden Cross): arr이 reference를 아래에서 위로 통과 → 1
        - 하향 교차(Death Cross): arr이 reference를 위에서 아래로 통과 → -1
        - 교차 없음: 0
        - 첫 번째 값은 항상 0 (이전 값 없음)

# shift
배열 이동(Shift). 배열을 앞뒤로 이동.

shift(arr: np.ndarray, periods: int = 1, fill_value: float = np.nan) -> np.ndarray
    배열을 지정된 기간만큼 이동

    Args:
        arr: 입력 데이터 배열
        periods: 이동 기간 (양수: 뒤로, 음수: 앞으로)
        fill_value: 빈 공간을 채울 값 (기본값: NaN)

    Returns:
        np.ndarray: 이동된 배열, 입력과 동일한 길이

    Notes:
        - periods > 0: 배열을 뒤로 이동 (앞쪽 periods개를 fill_value로 채움)
        - periods < 0: 배열을 앞으로 이동 (뒤쪽 |periods|개를 fill_value로 채움)
        - periods == 0: 원본 배열 반환

---

**사용 예시:**
```python
import numpy as np
from financial_indicators.core.series import scaling, pct_change, crossover

# 샘플 데이터
prices = np.array([100, 102, 101, 103, 105, 104, 106])

# Min-Max 스케일링 (0-1)
scaled = scaling(prices, min_val=0.0, max_val=1.0)
# [0.0, 0.333, 0.167, 0.5, 0.833, 0.667, 1.0]

# 퍼센트 변화율 (1일)
pct = pct_change(prices, periods=1)
# [NaN, 0.02, -0.0098, 0.0198, 0.0194, -0.0095, 0.0192]

# 교차 탐지
sma_short = np.array([100, 101, 102, 103, 104, 105, 106])
sma_long = np.array([101, 102, 103, 102, 103, 104, 105])
signal = crossover(sma_short, sma_long)
# [0, 0, 0, 1, 0, 0, 0]  # 3번째 인덱스에서 상향 교차
```

**의존성:**
- 모든 함수는 독립적 (내부 함수 호출 없음)
