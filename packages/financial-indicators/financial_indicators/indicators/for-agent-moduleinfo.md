# Indicator Functions

DataFrame 기반 기술 지표 계산 함수. Core Functions를 조합하여 캔들 데이터로부터 지표를 계산한다.

## 특징

- **순수 함수**: stateless, 부수효과 없음
- **DataFrame 입력**: OHLCV 캔들 데이터
- **유연한 반환**: 단일 값은 np.ndarray, 다중 값은 dict[str, np.ndarray]
- **NaN 패딩**: 출력 길이는 항상 입력과 동일

## 함수 목록

# calculate_sma
단순이동평균(Simple Moving Average) 계산. close 가격의 SMA를 반환.

calculate_sma(candle_df: pd.DataFrame, period: int = 20) -> np.ndarray
    ValueError: 'close' 컬럼 누락, period < 1
    close 가격의 단순이동평균 계산

# calculate_ema
지수이동평균(Exponential Moving Average) 계산. close 가격의 EMA를 반환.

calculate_ema(candle_df: pd.DataFrame, period: int = 12) -> np.ndarray
    ValueError: 'close' 컬럼 누락, period < 1
    close 가격의 지수이동평균 계산

# calculate_rsi
RSI(Relative Strength Index) 계산. 0-100 범위의 값 반환.

calculate_rsi(candle_df: pd.DataFrame, period: int = 14, use: str = 'close') -> np.ndarray
    ValueError: 컬럼 누락, period < 1
    RSI 계산 (기본값: 0-100 범위)

# calculate_rsi_entropy
RSI Entropy 계산. RSI와 엔트로피 기반 신호를 포함한 dict 반환.

calculate_rsi_entropy(candle_df: pd.DataFrame, rsi_period: int = 20, rsi_use: str = 'close', entropy_window: int = 365) -> dict[str, np.ndarray]
    ValueError: 컬럼 누락, period < 1, window < 2
    RSI Entropy 계산, 다중 값 반환

---

**사용 예시:**
```python
import pandas as pd
from financial_indicators.indicators import calculate_sma, calculate_rsi

# 캔들 데이터
candle_df = pd.DataFrame({
    'timestamp': [1609459200, 1609545600, ...],
    'open': [29000.0, 29100.0, ...],
    'high': [29500.0, 29600.0, ...],
    'low': [28800.0, 29000.0, ...],
    'close': [29200.0, 29400.0, ...],
    'volume': [1000.0, 1200.0, ...]
})

# 단일 값 지표
sma_20 = calculate_sma(candle_df, period=20)  # np.ndarray
rsi_14 = calculate_rsi(candle_df, period=14)  # np.ndarray

# 다중 값 지표
rsi_entropy = calculate_rsi_entropy(candle_df, rsi_period=14, entropy_window=365)
# {
#     'base': np.ndarray,
#     'z-1': np.ndarray,
#     'z+1': np.ndarray,
#     'buy': np.ndarray,
#     'sell': np.ndarray
# }
```

**반환 형식:**
- 단일 값: `np.ndarray` (길이 = len(candle_df))
- 다중 값: `dict[str, np.ndarray]` (각 배열 길이 = len(candle_df))

**의존성:**
- calculate_sma → core.rolling.sma
- calculate_ema → core.rolling.ema
- calculate_rsi → core.rolling.ema, core.series.pct_change
- calculate_rsi_entropy → calculate_rsi, core.rolling.std, core.series.scaling
