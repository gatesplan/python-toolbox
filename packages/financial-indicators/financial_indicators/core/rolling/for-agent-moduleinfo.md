# sma
단순이동평균(Simple Moving Average) 계산. NumPy convolution 기반 고속 연산.

sma(arr: np.ndarray, window: int) -> np.ndarray
    배열에 대한 단순이동평균 계산

    Args:
        arr: 입력 데이터 배열
        window: 이동평균 윈도우 크기

    Returns:
        np.ndarray: SMA 결과, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: window < 1인 경우

    Notes:
        - window >= len(arr)인 경우: cumulative mean 반환
        - window == 1인 경우: 원본 배열 반환
        - 그 외: convolution 사용하여 계산
        - 계산 불가능한 초기 window-1개 값은 cumulative mean으로 패딩

# ema
지수이동평균(Exponential Moving Average) 계산. 순차 계산 구현.

ema(arr: np.ndarray, span: int) -> np.ndarray
    배열에 대한 지수이동평균 계산

    Args:
        arr: 입력 데이터 배열
        span: EMA 스팬 (기간)

    Returns:
        np.ndarray: EMA 결과, 입력과 동일한 길이

    Raises:
        ValueError: span < 1인 경우

    Notes:
        - alpha = 2.0 / (span + 1.0)
        - 첫 번째 값은 arr[0]로 초기화
        - 이후 값은 EMA[i] = alpha * arr[i] + (1 - alpha) * EMA[i-1]

# wma
가중이동평균(Weighted Moving Average) 계산. 선형 가중치 적용.

wma(arr: np.ndarray, window: int) -> np.ndarray
    배열에 대한 가중이동평균 계산

    Args:
        arr: 입력 데이터 배열
        window: 가중 이동평균 윈도우 크기

    Returns:
        np.ndarray: WMA 결과, 입력과 동일한 길이

    Raises:
        ValueError: window < 1인 경우

    Notes:
        - 가중치: [1, 2, 3, ..., window] (선형 증가)
        - 최근 값에 더 높은 가중치 부여
        - 초기 window-1개 값은 현재 가용 데이터로 계산

# std
롤링 표준편차(Rolling Standard Deviation) 계산.

std(arr: np.ndarray, window: int, ddof: int = 1) -> np.ndarray
    배열에 대한 롤링 표준편차 계산

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기
        ddof: 자유도 보정 (기본값: 1, 표본 표준편차)

    Returns:
        np.ndarray: 표준편차 결과, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: window < 2인 경우 (표준편차 계산 불가)

    Notes:
        - ddof=0: 모집단 표준편차
        - ddof=1: 표본 표준편차 (기본값)
        - 초기 window-1개 값은 NaN

# max
롤링 최댓값(Rolling Maximum) 계산.

max(arr: np.ndarray, window: int) -> np.ndarray
    배열에 대한 롤링 최댓값 계산

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기

    Returns:
        np.ndarray: 롤링 최댓값 결과, 입력과 동일한 길이

    Raises:
        ValueError: window < 1인 경우

    Notes:
        - 초기 window-1개 값은 현재까지의 최댓값

# min
롤링 최솟값(Rolling Minimum) 계산.

min(arr: np.ndarray, window: int) -> np.ndarray
    배열에 대한 롤링 최솟값 계산

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기

    Returns:
        np.ndarray: 롤링 최솟값 결과, 입력과 동일한 길이

    Raises:
        ValueError: window < 1인 경우

    Notes:
        - 초기 window-1개 값은 현재까지의 최솟값

# zscore
롤링 Z-Score 계산. SMA와 STD를 조합하여 표준화 점수 계산.

zscore(arr: np.ndarray, window: int, ddof: int = 1) -> np.ndarray
    배열에 대한 롤링 Z-Score 계산

    Args:
        arr: 입력 데이터 배열
        window: 롤링 윈도우 크기
        ddof: 자유도 보정 (기본값: 1)

    Returns:
        np.ndarray: Z-Score 결과, 입력과 동일한 길이 (초기값 NaN 패딩)

    Raises:
        ValueError: window < 2인 경우

    Notes:
        - zscore = (arr - rolling_mean) / rolling_std
        - std가 0인 경우 해당 위치는 0으로 처리 (0 나누기 방지)
        - 내부적으로 sma()와 std() 함수 사용

---

**사용 예시:**
```python
import numpy as np
from financial_indicators.core.rolling import sma, ema, zscore

# 샘플 데이터
prices = np.array([100, 102, 101, 103, 105, 104, 106])

# 단순이동평균 (3일)
sma_3 = sma(prices, window=3)
# [100.0, 101.0, 101.0, 102.0, 103.0, 104.0, 105.0]

# 지수이동평균 (5일)
ema_5 = ema(prices, span=5)

# Z-Score (5일)
z = zscore(prices, window=5)
```

**의존성:**
- zscore → sma, std (내부 호출)
- 나머지 함수는 독립적
