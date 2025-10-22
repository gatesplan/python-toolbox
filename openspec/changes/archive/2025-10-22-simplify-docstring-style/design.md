# Design: Simplify Docstring Style

## Architectural Rationale

### Current Problem
현재 docstring 작성 방식은 전통적인 문서화 표준(Sphinx, Google/NumPy style)을 따르고 있으나, 이는 다음 환경을 가정합니다:
- 사람이 직접 코드를 읽고 이해
- API 문서 자동 생성 도구 사용
- 타입 정보가 없는 동적 언어 환경

### Why Change?
본 프로젝트는 다음 특징을 가집니다:
1. **에이전트 위임 개발**: AI 에이전트가 코드를 읽고 작성
2. **타입 힌트 완비**: Python 3.10+ 타입 힌트로 모든 시그니처 표현
3. **테스트 주도**: Example보다 실제 테스트 코드가 더 신뢰성 높음
4. **빠른 반복**: 장황한 docstring 동기화가 개발 속도 저하

### Design Principles

#### 1. Single Line of Intent
메서드는 **무엇을 하는가**만 설명합니다. **어떻게 하는가**는 코드로, **왜 하는가**는 Architecture 문서로 설명합니다.

```python
# BAD: 너무 상세
def get_price_sample(...) -> float:
    """
    정규분포에서 가격을 샘플링하고 범위 내로 클리핑.

    Args:
        min: 최소 가격
        max: 최대 가격
        mean: 정규분포 평균
        std: 정규분포 표준편차
        min_z: 최소 z-score (기본값: -2.0)
        max_z: 최대 z-score (기본값: 2.0)

    Returns:
        float: [min, max] 범위 내의 샘플링된 가격
    """

# GOOD: 의도만 전달
def get_price_sample(...) -> float:
    """정규분포 기반 가격 샘플링 (범위 클리핑 적용)."""
```

#### 2. Type Hints Replace Args/Returns
타입 힌트가 이미 완전한 시그니처 정보를 제공하므로, docstring에서 반복하지 않습니다.

```python
# Type hints already tell the full story
def round_to_min_amount(self, amount: float, min_amount: float) -> float:
    """금액을 최소 거래 단위의 배수로 내림."""
```

#### 3. Class Docstring: Responsibility Only
클래스는 **책임 범위**와 **핵심 특성**만 설명합니다. 개별 메서드 설명은 각 메서드 docstring에 위임합니다.

```python
# BAD: 메서드 나열
class CalculationTool:
    """
    시뮬레이션에 필요한 수치 계산을 제공하는 도구 클래스.

    모든 메서드는 stateless하며 순수 함수입니다.

    주요 메서드:
    - round_to_min_amount: 금액 반올림
    - get_price_sample: 가격 샘플링
    - get_separated_amount_sequence: 금액 분할
    - get_price_range: 가격 범위 판단
    """

# GOOD: 책임과 특성만
class CalculationTool:
    """시뮬레이션 수치 계산 도구 (stateless 순수 함수)."""
```

#### 4. No Examples in Docstrings
Example 코드는 다음 이유로 제거합니다:
- 테스트 코드가 더 신뢰성 있는 예시 제공
- Docstring 예시는 코드 변경 시 동기화 누락 위험
- 에이전트는 테스트 코드를 직접 읽는 것이 더 효율적

```python
# BAD: Example in docstring
def round_to_min_amount(self, amount: float, min_amount: float) -> float:
    """
    금액을 최소 거래 단위의 배수로 내림.

    Example:
        >>> calc = CalculationTool()
        >>> calc.round_to_min_amount(1.234, 0.01)
        1.23
    """

# GOOD: Example in test
def test_round_to_min_amount_basic(self):
    calc = CalculationTool()
    result = calc.round_to_min_amount(1.234, 0.01)
    assert result == 1.23
```

### Trade-offs

#### Gains
- **토큰 효율성**: 에이전트가 더 빠르게 코드 이해
- **유지보수 부담 감소**: 동기화할 문서가 줄어듦
- **가독성 향상**: 핵심 의도에 집중
- **일관성**: 모든 메서드가 동일한 스타일

#### Costs
- **신규 개발자 온보딩**: 상세 설명 부족 (Architecture 문서로 보완)
- **API 문서 생성**: Sphinx 등 자동 문서화 도구와 호환성 저하 (현재 미사용)

### Impact on Existing Systems
- **테스트**: 영향 없음 (docstring은 런타임 동작과 무관)
- **CI/CD**: 영향 없음
- **에이전트 워크플로우**: 긍정적 (더 빠른 이해)
- **Architecture 문서**: 영향 없음 (별도 관리)

## Implementation Strategy

### Step-by-Step Approach
1. 각 파일을 독립적으로 수정 (병렬 작업 가능)
2. 수정 후 즉시 해당 파일의 테스트 실행
3. 모든 수정 완료 후 전체 테스트 실행
4. Git diff로 로직 변경 없음 확인

### Rollback Plan
- Git commit 단위로 작업하여 필요 시 revert 가능
- 테스트 실패 시 해당 파일만 rollback

## Future Considerations
- 다른 패키지(`financial-assets`, `financial-indicators`)에도 동일 정책 적용 검토
- 프로젝트 전체 docstring 컨벤션 문서화 (`CLAUDE.md` 또는 `project.md`에 추가)
