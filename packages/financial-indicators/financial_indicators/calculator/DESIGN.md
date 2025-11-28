# IndicatorCalculator - Design Document

## 패턴 선택

**Simple Class Pattern**

IndicatorCalculator는 CPSCP나 SDW 같은 복잡한 패턴이 필요 없는 단순한 구조입니다.

**선택 이유:**
- 단일 책임: 지표 계산 조율 + 캐싱
- Registry에 위임: 실제 계산은 indicator functions가 담당
- 상태 단순: 캐시 딕셔너리 하나만 유지
- 확장성: 새 지표는 Registry에 등록되므로 Calculator 코드 수정 불필요

**부적합한 패턴:**
- CPSCP: 5계층이 필요할 정도로 복잡하지 않음
- SDW: 여러 Director/Worker가 필요한 다양한 작업이 아님

## 컴포넌트 구조

### IndicatorCalculator (단일 클래스)

**책임:**
- 사용자 진입점 (public API)
- 지표 계산 조율 (Registry를 통한 함수 조회 및 실행)
- 계산 결과 캐싱 (중복 계산 방지)
- 배치 계산 지원 (여러 지표 한 번에)
- 캐시 관리 (clear, get 등)

**특징:**
- Stateful (캐시 딕셔너리 유지)
- IndicatorRegistry에 의존
- Thread-safe 고려 필요 (optional, 나중에 추가 가능)

**주요 메서드:**
- `__init__(registry)`: IndicatorCalculator 초기화, registry 주입
- `calculate(name, candle_df, **kwargs)`: 단일 지표 계산 (캐싱 적용)
- `calculate_batch(requests, candle_df)`: 여러 지표 일괄 계산
- `clear_cache()`: 전체 캐시 초기화
- `get_cache_size()`: 캐시 크기 반환 (디버깅용)

## 디렉토리 구조

```
financial_indicators/
├── calculator/
│   ├── __init__.py              # IndicatorCalculator export
│   ├── calculator.py            # IndicatorCalculator 클래스
│   ├── DESIGN.md                # 이 문서
│   └── for-agent-moduleinfo.md  # Agent용 참조 문서
```

**파일 설명:**
- `calculator.py`: IndicatorCalculator 클래스 정의
- `__init__.py`: IndicatorCalculator export
- `for-agent-moduleinfo.md`: 클래스 상세 API 문서

## 사용 패턴

### 기본 사용

```python
from financial_indicators.calculator import IndicatorCalculator
from financial_indicators.registry import registry
import pandas as pd

# Calculator 생성
calculator = IndicatorCalculator(registry)

# DataFrame 준비
candle_df = pd.DataFrame({
    'timestamp': [...],
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# 단일 지표 계산
sma_20 = calculator.calculate("sma", candle_df, period=20)
rsi_14 = calculator.calculate("rsi", candle_df, period=14)

# 같은 파라미터로 재계산 시 캐시 사용 (빠름)
sma_20_cached = calculator.calculate("sma", candle_df, period=20)
```

### 배치 계산

```python
# 여러 지표 한 번에 계산
results = calculator.calculate_batch([
    {"name": "sma", "period": 20},
    {"name": "sma", "period": 50},
    {"name": "ema", "period": 12},
    {"name": "rsi", "period": 14},
    {"name": "rsi_entropy", "rsi_period": 20, "entropy_window": 365}
], candle_df)

# results = {
#     "sma_20": np.ndarray,
#     "sma_50": np.ndarray,
#     "ema_12": np.ndarray,
#     "rsi_14": np.ndarray,
#     "rsi_entropy_20_365": {
#         "base": np.ndarray,
#         "z-1": np.ndarray,
#         ...
#     }
# }
```

### 캐시 관리

```python
# 캐시 크기 확인
size = calculator.get_cache_size()
print(f"Cached: {size} results")

# 캐시 초기화
calculator.clear_cache()
```

## 구현 세부사항

### 데이터 구조

```python
class IndicatorCalculator:
    def __init__(self, registry):
        self._registry = registry
        self._cache: Dict[str, Union[np.ndarray, Dict[str, np.ndarray]]] = {}
```

### 캐시 키 생성

캔들 데이터 + 지표 이름 + 파라미터를 기반으로 고유 키 생성:

```python
def _generate_cache_key(self, name: str, candle_df: pd.DataFrame, **kwargs) -> str:
    # DataFrame identity (id 또는 hash)
    df_id = id(candle_df)

    # 파라미터를 정렬된 문자열로 변환
    params_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))

    # 최종 키: "name_df_id_params"
    return f"{name}_{df_id}_{params_str}" if params_str else f"{name}_{df_id}"
```

**주의:**
- DataFrame의 `id()`를 사용하면 같은 객체만 캐시 히트
- 더 정교한 캐싱은 DataFrame 해시 사용 (선택적)

### 배치 계산 최적화

```python
def calculate_batch(self, requests: List[Dict], candle_df: pd.DataFrame) -> Dict:
    results = {}

    for req in requests:
        name = req.pop("name")
        result_key = self._generate_result_key(name, **req)

        # 캐시 확인 후 계산
        result = self.calculate(name, candle_df, **req)
        results[result_key] = result

    return results

def _generate_result_key(self, name: str, **kwargs) -> str:
    params_str = "_".join(str(v) for v in kwargs.values())
    return f"{name}_{params_str}" if params_str else name
```

## 확장성

### 캐시 전략 확장

현재는 메모리 기반 딕셔너리 캐시이지만, 나중에 확장 가능:
- LRU 캐시 (크기 제한)
- TTL 기반 캐시 (시간 만료)
- 파일 기반 캐시
- Redis 등 외부 캐시

### 의존성 최적화 (향후)

배치 계산 시 지표 간 의존성 분석:
- RSI Entropy는 RSI를 재사용
- 같은 SMA period는 한 번만 계산

현재는 단순 구현, 나중에 최적화 추가 가능

## 테스트 전략

- 계산 테스트: Registry를 통한 지표 함수 실행
- 캐싱 테스트: 같은 요청 시 캐시 히트 확인
- 배치 테스트: 여러 지표 일괄 계산
- 캐시 관리 테스트: clear, size 확인
- 다중 값 지표 테스트: rsi_entropy 같은 dict 반환 처리

## 의존성

**Depends on:**
- IndicatorRegistry: 지표 함수 조회

**Used by:**
- 사용자 코드 (최상위 API)
