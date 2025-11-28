# IndicatorCalculator

지표 계산 조율 및 캐싱을 담당하는 계산기. Registry를 통해 지표 함수를 조회하고 실행하며, 결과를 캐싱하여 중복 계산을 방지한다.

_registry: IndicatorRegistry    # 지표 함수 조회용 Registry
_cache: Dict[str, Union[np.ndarray, Dict[str, np.ndarray]]]    # 계산 결과 캐시

## 초기화

__init__(registry: IndicatorRegistry) -> None
    IndicatorCalculator 초기화

    Args:
        registry: IndicatorRegistry 인스턴스 (지표 함수 조회용)

## 단일 지표 계산

calculate(name: str, candle_df: pd.DataFrame, **kwargs) -> Union[np.ndarray, Dict[str, np.ndarray]]
    지표 계산 (캐싱 적용)

    Args:
        name: 지표 이름 (예: "sma", "ema", "rsi", "rsi_entropy")
        candle_df: OHLCV 캔들 데이터 DataFrame
        **kwargs: 지표별 파라미터 (예: period=20, use='close')

    Returns:
        Union[np.ndarray, Dict[str, np.ndarray]]:
            - 단일 값 지표: np.ndarray (길이 = len(candle_df))
            - 다중 값 지표: dict[str, np.ndarray] (예: rsi_entropy)

    Raises:
        IndicatorNotFoundError: Registry에 등록되지 않은 지표인 경우
        ValueError: 지표 함수가 발생시키는 검증 오류

    Notes:
        - 캐시 키: name + DataFrame id + sorted kwargs
        - 같은 DataFrame 객체 + 같은 파라미터면 캐시 히트
        - 캐시 히트 시 계산 없이 저장된 결과 반환

## 배치 계산

calculate_batch(requests: List[Dict[str, Any]], candle_df: pd.DataFrame, clear_cache: bool = True) -> Dict[str, Union[np.ndarray, Dict[str, np.ndarray]]]
    여러 지표 일괄 계산

    Args:
        requests: 지표 요청 리스트, 각 요청은 {"name": str, **params} 형태
            예: [
                {"name": "sma", "period": 20},
                {"name": "ema", "period": 12},
                {"name": "rsi", "period": 14}
            ]
        candle_df: OHLCV 캔들 데이터 DataFrame
        clear_cache: 배치 계산 전 캐시 클리어 여부 (기본값: True)

    Returns:
        Dict[str, Union[np.ndarray, Dict[str, np.ndarray]]]:
            결과 딕셔너리, 키는 "name_params" 형식
            예: {
                "sma_20": np.ndarray,
                "ema_12": np.ndarray,
                "rsi_14": np.ndarray
            }

    Notes:
        - 기본적으로 배치 계산 전 캐시를 클리어 (여러 종목 처리 시 안전)
        - clear_cache=False로 설정하면 기존 캐시 유지
        - 각 지표는 독립적으로 계산 (캐싱 적용)
        - 결과 키는 _generate_result_key로 생성
        - 요청 리스트의 원본은 수정되지 않음 (복사 후 처리)

## 캐시 관리

clear_cache() -> None
    전체 캐시 초기화

    Notes:
        - 모든 캐시된 계산 결과 삭제
        - 메모리 해제 목적으로 사용

get_cache_size() -> int
    현재 캐시된 항목 수 반환

    Returns:
        int: 캐시에 저장된 결과 개수

---

**사용 예시:**

```python
from financial_indicators.calculator import IndicatorCalculator
from financial_indicators.registry import registry
import pandas as pd
import numpy as np

# 1. Calculator 생성
calculator = IndicatorCalculator(registry)

# 2. 캔들 데이터 준비
candle_df = pd.DataFrame({
    'timestamp': np.arange(1609459200, 1609459200 + 100 * 86400, 86400),
    'open': np.random.rand(100) * 100 + 100,
    'high': np.random.rand(100) * 100 + 105,
    'low': np.random.rand(100) * 100 + 95,
    'close': np.random.rand(100) * 100 + 100,
    'volume': np.random.rand(100) * 1000 + 500
})

# 3. 단일 지표 계산
sma_20 = calculator.calculate("sma", candle_df, period=20)
print(f"SMA length: {len(sma_20)}")  # 100

# 4. 다른 파라미터로 계산
sma_50 = calculator.calculate("sma", candle_df, period=50)

# 5. 같은 요청 -> 캐시 히트 (빠름)
sma_20_cached = calculator.calculate("sma", candle_df, period=20)
assert np.array_equal(sma_20, sma_20_cached)

# 6. RSI 계산
rsi_14 = calculator.calculate("rsi", candle_df, period=14)

# 7. 다중 값 지표 (dict 반환)
rsi_entropy = calculator.calculate("rsi_entropy", candle_df,
                                   rsi_period=20, entropy_window=365)
print(rsi_entropy.keys())  # dict_keys(['base', 'z-1', 'z+1', 'buy', 'sell'])

# 8. 배치 계산 (기본: 캐시 자동 클리어)
results = calculator.calculate_batch([
    {"name": "sma", "period": 20},
    {"name": "sma", "period": 50},
    {"name": "ema", "period": 12},
    {"name": "rsi", "period": 14}
], candle_df)

print(results.keys())
# dict_keys(['sma_20', 'sma_50', 'ema_12', 'rsi_14'])

# 여러 종목 처리 (각 종목마다 캐시 자동 클리어)
for ticker in ['BTC', 'ETH', 'SOL']:
    df = get_candle(ticker)
    results = calculator.calculate_batch([
        {"name": "sma", "period": 20},
        {"name": "rsi", "period": 14}
    ], df)  # clear_cache=True (기본값)

# 같은 데이터로 반복 호출 시 캐시 유지
df = get_candle('BTC')
results1 = calculator.calculate_batch([...], df, clear_cache=False)
results2 = calculator.calculate_batch([...], df, clear_cache=False)  # 캐시 활용

# 9. 캐시 관리
print(f"Cache size: {calculator.get_cache_size()}")  # 6 (sma_20, sma_50, ema_12, rsi_14, rsi_entropy)
calculator.clear_cache()
print(f"Cache size: {calculator.get_cache_size()}")  # 0
```

**캐시 동작:**

```python
# DataFrame 객체가 같으면 캐시 히트
df = pd.DataFrame({'close': [100, 101, 102]})

result1 = calculator.calculate("sma", df, period=3)  # 계산
result2 = calculator.calculate("sma", df, period=3)  # 캐시 히트

# DataFrame 객체가 다르면 캐시 미스 (내용이 같아도)
df2 = pd.DataFrame({'close': [100, 101, 102]})
result3 = calculator.calculate("sma", df2, period=3)  # 다시 계산 (df2는 다른 객체)
```

**배치 계산 결과 키:**

```python
# 결과 키 생성 규칙
requests = [
    {"name": "sma", "period": 20},           # -> "sma_20"
    {"name": "rsi", "period": 14, "use": "close"},  # -> "rsi_14_close"
    {"name": "rsi_entropy", "rsi_period": 20, "entropy_window": 365}  # -> "rsi_entropy_20_365"
]
```

**의존성:**
- IndicatorRegistry: registry.get(name) 메서드 사용
- pandas: DataFrame 처리
- numpy: 배열 타입 확인

**캐시 키 생성 로직:**

```python
def _generate_cache_key(name: str, candle_df: pd.DataFrame, **kwargs) -> str:
    df_id = id(candle_df)
    params_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return f"{name}_{df_id}_{params_str}" if params_str else f"{name}_{df_id}"

# 예시:
# name="sma", df_id=140234567890, period=20
# -> "sma_140234567890_period=20"
```

**결과 키 생성 로직:**

```python
def _generate_result_key(name: str, **kwargs) -> str:
    params_str = "_".join(str(v) for v in kwargs.values())
    return f"{name}_{params_str}" if params_str else name

# 예시:
# name="sma", period=20 -> "sma_20"
# name="rsi", period=14, use="close" -> "rsi_14_close"
```

**멀티프로세스/멀티스레드 환경:**

멀티프로세스:
- 각 프로세스에서 Calculator를 새로 생성
- Registry는 import 시점에 자동 재생성 (decorator 재실행)
- DataFrame은 pickle 가능하므로 프로세스 간 전달 가능
- 각 프로세스의 캐시는 독립적 (공유 불필요)

멀티스레드:
- 각 스레드마다 별도 Calculator 인스턴스 생성 권장
- Calculator는 가벼운 객체 (생성 비용 낮음)
- 스레드 간 캐시 공유 불필요

사용 예시 (ProcessPoolExecutor):
```python
from concurrent.futures import ProcessPoolExecutor
from financial_indicators.calculator import IndicatorCalculator
from financial_indicators.registry import registry

def worker(candle_df, name, **kwargs):
    calc = IndicatorCalculator(registry)
    return calc.calculate(name, candle_df, **kwargs)

with ProcessPoolExecutor() as executor:
    futures = [
        executor.submit(worker, df, "sma", period=20),
        executor.submit(worker, df, "rsi", period=14)
    ]
    results = [f.result() for f in futures]
```
