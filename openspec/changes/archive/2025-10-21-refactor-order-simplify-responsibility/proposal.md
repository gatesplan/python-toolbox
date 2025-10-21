# Refactor SpotOrder: Simplify Responsibility

## Why
SpotOrder는 현재 "열린 거래 표현"이라는 본래 책임을 넘어서 거래 처리 로직(fill 메서드를 통한 SpotTrade 생성)까지 포함하고 있습니다. 이로 인해:
- Order 모듈이 Trade 모듈에 강하게 결합되어 단일 책임 원칙(SRP)을 위반
- 외부에서 거래 처리 로직을 유연하게 구성하기 어려움
- fill 메서드가 SpotTrade 생성과 Order 상태 업데이트를 동시에 수행하여 책임이 불명확

## What Changes
- **BREAKING**: 기존 `fill_by_asset_amount()` 및 `fill_by_value_amount()` 메서드를 SpotTrade 생성 로직 제거한 형태로 변경
  - SpotTrade 객체 반환 제거 (외부에서 생성)
  - 대신 불변 복제 패턴으로 변경: 원본 유지 + 업데이트된 새 SpotOrder 반환
- **BREAKING**: `cancel()` 메서드 제거
- **ADDED**: 상태 변경 편의 메서드 추가
  - `to_pending_state()`: pending 상태로 복제
  - `to_partial_state()`: partial 상태로 복제
  - `to_filled_state()`: filled 상태로 복제
  - `to_canceled_state()`: canceled 상태로 복제
  - 모두 불변 복제 패턴: 기존 내용 복제 + 상태만 변경한 새 인스턴스 반환
- **ADDED**: `fee_rate` 필드 추가
  - 거래 수수료 비율 정보 (예: 0.001 = 0.1%)
  - Order가 거래 처리에 필요한 모든 정보를 포함하여 stateless 처리 가능
  - 외부에서 SpotTrade 생성 시 `order.fee_rate`를 사용해 fee 계산
- SpotOrder는 순수하게 주문 정보 표현 및 불변 업데이트 편의 기능 제공
- 거래 처리 로직(SpotTrade 생성)은 완전히 외부로 분리하되, 필요한 모든 정보는 Order가 제공

## Impact
- **BREAKING CHANGE**: 기존 fill 메서드의 반환값이 변경됨 (SpotTrade → SpotOrder)
- Affected specs: `order-data-structure`
- Affected code:
  - `packages/financial-assets/financial_assets/order/spot_order.py`
  - `packages/financial-assets/tests/test_order.py`
  - SpotOrder.fill 메서드를 사용하는 외부 거래 처리 로직 (존재한다면)
