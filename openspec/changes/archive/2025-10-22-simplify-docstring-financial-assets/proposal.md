# Proposal: Simplify Docstring Style for Financial-Assets

## Change ID
`simplify-docstring-financial-assets`

## Overview
financial-assets 패키지의 docstring이 표준 문서화 규칙(Sphinx/Google style)을 따르고 있어 과도하게 상세합니다. financial-simulation 패키지에 적용한 것과 동일한 간결한 한글 docstring 스타일을 적용하여 에이전트 위임 개발 환경에 최적화합니다.

## Why
financial-simulation 패키지에서 docstring 간소화 작업을 완료하여 83% 코드 감소(441줄 → 73줄)와 토큰 효율성 개선을 달성했습니다. financial-assets 패키지에도 동일한 문제가 존재합니다:

1. **일관성**: financial-simulation과 동일한 스타일로 통일 필요
2. **토큰 낭비**: Attributes, Args, Returns, Examples 섹션이 타입 힌트와 중복
3. **유지보수 부담**: 장황한 docstring이 코드 변경 시 동기화 부담 증가
4. **에이전트 효율**: AI는 간결한 메타데이터만으로 충분히 이해 가능

## Problem Statement
- SpotOrder, SpotTrade, SpotWallet 등 핵심 클래스에 20~50줄의 장황한 docstring
- 모든 메서드에 Args, Returns, Examples, Raises 섹션 포함
- 타입 힌트로 이미 표현된 정보가 docstring에 중복 기록
- 영어/한글 혼용으로 스타일 불일치

## Goals
1. 모든 docstring을 한글로 통일
2. 클래스 docstring: 책임 범위만 2~3줄로 요약
3. 메서드 docstring: 한 줄 기능 설명만 유지
4. Attributes/Args/Returns/Examples/Raises 섹션 제거
5. 타입 힌트 유지 (제거하지 않음)
6. 전체 테스트 통과 (기능 변경 없음)

## Scope
### In Scope
- `packages/financial-assets/financial_assets/` 핵심 모듈:
  - `order/spot_order.py`
  - `trade/spot_trade.py`
  - `trade/spot_side.py`
  - `wallet/spot_wallet.py`
  - `wallet/wallet_inspector.py`
  - `ledger/spot_ledger.py`
  - `ledger/spot_ledger_entry.py`
  - `pair/pair.py`
  - `pair/pair_stack.py`
  - `token/token.py`
  - `stock_address/stock_address.py`
  - `price/Price.py`

### Out of Scope
- 테스트 코드 docstring (현재 상태 유지)
- Candle storage 관련 모듈 (별도 작업으로 분리)
- Wallet workers (별도 작업으로 분리)

## Constraints
- 타입 힌트는 유지 (제거하지 않음)
- 기존 로직 변경 없음 (docstring만 수정)
- 클래스 책임 설명은 필수 유지
- 불변 객체 특성 유지 (@dataclass, immutable pattern)

## Success Criteria
1. 각 클래스 docstring이 3줄 이내로 책임 범위 설명
2. 각 메서드 docstring이 1줄로 기능 목적 설명
3. Attributes/Args/Returns/Examples 섹션 모두 제거
4. 전체 테스트 통과 (기능 변경 없음 검증)
5. financial-simulation과 스타일 일관성 유지

## Related Specs
- `order-data-structure`
- `trade-data-structure`
- `wallet-data-structure`
- `spot-ledger-data-structure`
- `wallet-inspector`
- `simplify-docstring-style` (financial-simulation 작업 참조)

## Implementation Notes
### Current Style Example (SpotOrder)
```python
class SpotOrder:
    """Represents a spot trading order with immutable update pattern.

    SpotOrder encapsulates all information needed for stateless trade processing,
    including order details, fill state, fees, and minimum trade constraints.
    All state modifications return new instances, preserving immutability.

    Attributes:
        order_id: Unique identifier for the order
        stock_address: Market information (exchange, trading pair, etc.)
        side: BUY or SELL
        order_type: "limit", "market", or "stop"
        price: Limit price (None for market orders)
        amount: Total order amount in base currency
        timestamp: Order creation time
        stop_price: Stop price for stop orders (optional)
        filled_amount: Amount already filled (default: 0.0)
        status: Order status - "pending", "partial", "filled", or "canceled"
        fee_rate: Trading fee rate (default: 0.0)
        min_trade_amount: Minimum trade unit for partial fills (optional)

    Example:
        >>> order = SpotOrder(...)
    """
```

### Target Style
```python
class SpotOrder:
    """
    현물 거래 주문 (불변 복제 패턴).
    주문 정보, 체결 상태, 수수료, 최소 거래 제약을 캡슐화합니다.
    """
```

**Key Changes:**
- 모든 docstring을 한글로 통일
- 클래스: 2-3줄 책임 설명
- 메서드: 1줄 기능 설명
- Attributes/Args/Returns/Examples 완전 제거
- 타입 힌트 유지

## Risks
- 기존 docstring에 의존하는 자동화 도구 영향 (현재 없음)
- 신규 개발자 온보딩 시 설명 부족 우려 (Architecture 문서로 보완)

## Open Questions
- 없음
