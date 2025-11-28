# IndicatorRegistry - Design Document

## 패턴 선택

**Simple Registry Pattern**

IndicatorRegistry는 CPSCP나 SDW 같은 복잡한 패턴이 필요 없는 단순한 구조입니다.

**선택 이유:**
- 단일 책임: 지표 함수 등록 및 조회만 담당
- 상태 최소화: 딕셔너리 하나로 충분
- 확장성: Decorator 기반으로 새 지표 추가 용이
- 의존성 없음: 다른 컴포넌트에 의존하지 않음

**부적합한 패턴:**
- CPSCP: 5계층이 필요할 정도로 복잡하지 않음
- SDW: 여러 Director/Worker가 필요한 다양한 작업이 아님

## 컴포넌트 구조

### IndicatorRegistry (단일 클래스)

**책임:**
- 지표 함수 등록 (decorator 기반)
- 이름 기반 함수 조회
- 등록된 지표 목록 제공

**특징:**
- Singleton 패턴 또는 모듈 레벨 global instance
- Stateful (등록된 함수들을 딕셔너리에 저장)
- Thread-safe 고려 불필요 (등록은 초기화 시점, 조회는 read-only)

**주요 메서드:**
- `register(name: str)`: Decorator, 함수를 registry에 등록
- `get(name: str)`: 이름으로 함수 조회
- `has(name: str)`: 등록 여부 확인
- `list_all()`: 등록된 모든 지표 이름 반환

## 디렉토리 구조

```
financial_indicators/
├── registry/
│   ├── __init__.py              # registry 인스턴스 export
│   ├── registry.py              # IndicatorRegistry 클래스
│   ├── DESIGN.md                # 이 문서
│   └── for-agent-moduleinfo.md  # Agent용 참조 문서
```

**파일 설명:**
- `registry.py`: IndicatorRegistry 클래스 정의 + global instance 생성
- `__init__.py`: `registry` 인스턴스와 `register` decorator export
- `for-agent-moduleinfo.md`: 클래스 상세 API 문서

## 사용 패턴

### 지표 등록 (Indicator Functions에서)

```python
from financial_indicators.registry import register

@register("sma")
def calculate_sma(candle_df: pd.DataFrame, period: int = 20) -> np.ndarray:
    # ...
    pass

@register("rsi")
def calculate_rsi(candle_df: pd.DataFrame, period: int = 14, use: str = 'close') -> np.ndarray:
    # ...
    pass
```

### 지표 조회 (IndicatorCalculator에서)

```python
from financial_indicators.registry import registry

# 함수 조회
sma_func = registry.get("sma")
result = sma_func(candle_df, period=20)

# 등록 확인
if registry.has("rsi"):
    rsi_func = registry.get("rsi")

# 모든 지표 목록
all_indicators = registry.list_all()  # ["sma", "ema", "rsi", "rsi_entropy"]
```

## 구현 세부사항

### 데이터 구조

```python
class IndicatorRegistry:
    def __init__(self):
        self._registry: Dict[str, Callable] = {}
```

### 자동 등록 메커니즘

Indicator Functions 모듈을 import할 때 자동으로 등록됩니다:

```python
# financial_indicators/indicators/__init__.py
from .sma import calculate_sma
from .ema import calculate_ema
from .rsi import calculate_rsi
from .rsi_entropy import calculate_rsi_entropy

# import 시점에 decorator 실행되어 자동 등록됨
```

### 에러 처리

```python
class IndicatorNotFoundError(KeyError):
    """등록되지 않은 지표 조회 시 발생"""
    pass

def get(self, name: str) -> Callable:
    if name not in self._registry:
        raise IndicatorNotFoundError(f"Indicator '{name}' not found in registry")
    return self._registry[name]
```

## 확장성

새 지표 추가 절차:
1. `indicators/` 폴더에 새 파일 작성
2. `@register("name")` decorator 추가
3. `indicators/__init__.py`에 import 추가

**기존 코드 수정 불필요** - Registry에 자동으로 등록됨

## 테스트 전략

- 등록 테스트: decorator가 함수를 올바르게 등록하는지
- 조회 테스트: get이 올바른 함수를 반환하는지
- 예외 테스트: 미등록 지표 조회 시 IndicatorNotFoundError 발생
- 목록 테스트: list_all이 모든 등록된 지표를 반환하는지
- 중복 등록 테스트: 같은 이름 재등록 시 경고 또는 덮어쓰기

## 의존성

**Depends on:** 없음 (최하위 컴포넌트)

**Used by:**
- IndicatorCalculator: 지표 함수 조회 및 실행
- Indicator Functions: decorator로 자동 등록 (import 시점)
