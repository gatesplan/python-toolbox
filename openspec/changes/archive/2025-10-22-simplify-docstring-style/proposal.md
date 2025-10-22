# Proposal: Simplify Docstring Style

## Change ID
`simplify-docstring-style`

## Overview
현재 코드베이스의 docstring이 PSR 또는 표준 준수를 위해 과도하게 상세한 메타데이터를 포함하고 있습니다. 에이전트 위임 개발 환경에서는 간결한 의도 전달만으로 충분하므로, 클래스와 메서드의 docstring을 최소한의 정보만 담도록 정제합니다.

## Why
현재 코드베이스의 docstring이 표준 문서화 규칙(Sphinx/Google style)을 과도하게 따르고 있습니다. 이는 전통적인 사람 중심 개발 환경에서는 유용하지만, 에이전트 위임 개발 환경에서는 비효율적입니다:

1. **토큰 낭비**: Args/Returns/Example 섹션이 타입 힌트와 중복
2. **이해도 저하**: 장황한 설명이 핵심 의도를 가림
3. **유지보수 부담**: 코드 변경 시 docstring 동기화 누락 위험
4. **에이전트 효율**: AI는 간결한 메타데이터만으로 충분히 이해 가능

본 변경은 에이전트가 코드를 더 빠르게 이해하고, 개발자가 docstring 동기화 부담 없이 코드에 집중할 수 있도록 docstring 스타일을 최소화합니다.

## Problem Statement
- 모든 메서드에 Args, Returns, Example이 포함된 장황한 docstring이 작성됨
- 타입 힌트로 이미 표현된 정보가 docstring에 중복 기록됨
- 에이전트가 읽기에 토큰 소비가 과도하고 핵심 의도 파악이 지연됨
- 코드 유지보수 시 docstring 동기화 부담 증가

## Goals
1. 모든 docstring을 한글로 작성
2. 클래스 docstring: 책임 범위와 핵심 역할 요약 (1~3줄 한글)
3. 메서드 docstring: 한 줄 한글 기능 설명만 유지
4. 타입 힌트와 중복되는 Args/Returns 제거
5. Example 코드 제거 (테스트 코드로 대체)
6. 코드 가독성과 에이전트 이해도 개선

## Scope
### In Scope
- `packages/financial-simulation/financial_simulation/tradesim/` 전체 모듈
  - `calculation_tool.py`
  - `trade_factory.py`
  - `spot_limit_worker.py`
  - `spot_market_buy.py`
  - `spot_market_sell.py`
  - `trade_simulation.py`

### Out of Scope
- 테스트 코드 docstring (현재 상태 유지)
- 다른 패키지 (`financial-assets`, `financial-indicators` 등)
- Architecture 문서 (별도 이슈로 관리)

## Constraints
- 타입 힌트는 유지 (제거하지 않음)
- 기존 로직 변경 없음 (docstring만 수정)
- 클래스 책임 설명은 필수 유지

## Success Criteria
1. 각 클래스 docstring이 3줄 이내로 책임 범위 설명
2. 각 메서드 docstring이 1줄로 기능 목적 설명
3. Args, Returns, Example 섹션 모두 제거
4. 전체 테스트 통과 (기능 변경 없음 검증)

## Related Specs
- `calculation-tool`
- `tradesim-integration`
- `spot-limit-buy-worker` (archived)
- `spot-limit-sell-worker` (archived)
- `spot-market-buy-worker`
- `spot-market-sell-worker`

## Implementation Notes
### Current Style Example
```python
class CalculationTool:
    """
    시뮬레이션에 필요한 수치 계산을 제공하는 도구 클래스.

    모든 메서드는 stateless하며 순수 함수입니다.
    """

    def round_to_min_amount(self, amount: float, min_amount: float) -> float:
        """
        금액을 최소 거래 단위의 배수로 내림.

        Args:
            amount: 반올림할 금액
            min_amount: 최소 거래 단위

        Returns:
            float: min_amount의 배수로 내림된 금액

        Example:
            >>> calc = CalculationTool()
            >>> calc.round_to_min_amount(1.234, 0.01)
            1.23
        """
```

### Target Style
```python
class CalculationTool:
    """시뮬레이션 수치 계산 도구 (stateless 순수 함수)."""

    def round_to_min_amount(self, amount: float, min_amount: float) -> float:
        """금액을 최소 거래 단위의 배수로 내림."""
```

**Key Changes:**
- 모든 docstring을 한글로 통일
- 클래스: 1줄 책임 설명
- 메서드: 1줄 기능 설명
- Args/Returns/Example 완전 제거

## Risks
- 기존 docstring에 의존하는 자동화 도구 영향 (현재 없음)
- 신규 개발자 온보딩 시 설명 부족 우려 (Architecture 문서로 보완)

## Open Questions
- 없음
