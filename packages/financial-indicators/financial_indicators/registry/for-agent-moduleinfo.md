# IndicatorRegistry

지표 함수 등록 및 조회를 담당하는 레지스트리. Decorator 기반 자동 등록으로 확장 가능한 플러그인 구조 제공.

_registry: Dict[str, Callable]    # 이름 → 함수 매핑

## 초기화

__init__() -> None
    IndicatorRegistry 초기화, 빈 레지스트리 생성

## 등록 (Decorator)

register(name: str) -> Callable[[Callable], Callable]
    지표 함수를 레지스트리에 등록하는 decorator

    Args:
        name: 지표 이름 (예: "sma", "ema", "rsi")

    Returns:
        Callable: 원본 함수를 반환하는 decorator

    Raises:
        ValueError: 이미 등록된 이름인 경우 (선택적, 덮어쓰기 허용 가능)

    Notes:
        - import 시점에 자동 실행되어 함수 등록
        - 원본 함수를 수정하지 않고 그대로 반환
        - 중복 등록 시 경고 로그 출력 (덮어쓰기)

## 조회

get(name: str) -> Callable
    등록된 지표 함수 조회

    Args:
        name: 지표 이름

    Returns:
        Callable: 등록된 지표 함수

    Raises:
        IndicatorNotFoundError: 등록되지 않은 지표인 경우

has(name: str) -> bool
    지표 등록 여부 확인

    Args:
        name: 지표 이름

    Returns:
        bool: 등록되어 있으면 True, 아니면 False

## 목록 조회

list_all() -> List[str]
    등록된 모든 지표 이름 목록 반환

    Returns:
        List[str]: 지표 이름 리스트 (정렬됨)

---

**사용 예시:**

```python
# 1. 지표 등록 (indicators/sma.py)
from financial_indicators.registry import register

@register("sma")
def calculate_sma(candle_df: pd.DataFrame, period: int = 20) -> np.ndarray:
    # ...
    return result

# 2. 지표 조회 및 실행 (calculator)
from financial_indicators.registry import registry

# 등록 확인
if registry.has("sma"):
    # 함수 조회
    sma_func = registry.get("sma")

    # 실행
    result = sma_func(candle_df, period=20)

# 모든 지표 목록
all_indicators = registry.list_all()
# ["ema", "rsi", "rsi_entropy", "sma"]

# 미등록 지표 조회 시 예외
try:
    func = registry.get("unknown")
except IndicatorNotFoundError as e:
    print(f"Error: {e}")
```

**Global Instance:**

```python
# financial_indicators/registry/__init__.py
from .registry import IndicatorRegistry

# 전역 singleton 인스턴스
registry = IndicatorRegistry()

# decorator는 전역 인스턴스의 메서드
register = registry.register

__all__ = ["registry", "register"]
```

**자동 등록 메커니즘:**

```python
# financial_indicators/indicators/__init__.py
# import 시 decorator 실행되어 자동 등록
from .sma import calculate_sma       # @register("sma") 실행
from .ema import calculate_ema       # @register("ema") 실행
from .rsi import calculate_rsi       # @register("rsi") 실행
from .rsi_entropy import calculate_rsi_entropy  # @register("rsi_entropy") 실행
```

**의존성:**
- 없음 (최하위 컴포넌트, 표준 라이브러리만 사용)

**예외 클래스:**

```python
class IndicatorNotFoundError(KeyError):
    """등록되지 않은 지표 조회 시 발생하는 예외"""
    pass
```

**Thread Safety:**
- 등록은 모듈 import 시점 (단일 스레드)
- 조회는 read-only 작업
- 추가적인 동기화 불필요
