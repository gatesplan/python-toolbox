# Proposal: add-min-trade-amount

## Why
시뮬레이션 환경에서 주문을 분할하거나 부분 체결을 처리할 때, 실제 거래소의 최소 거래 단위 제약을 반영해야 합니다. 현재 SpotOrder는 최소 거래 단위 정보가 없어 비현실적인 소수점 단위 체결이 가능합니다.

실제 거래소에서는 각 마켓별로 최소 주문 수량(예: BTC 0.001개, ETH 0.01개)이 정해져 있으며, 이보다 작은 수량으로는 거래할 수 없습니다. 시뮬레이션의 정확도를 높이기 위해 이 제약을 Order 데이터에 포함해야 합니다.

## What Changes
- SpotOrder에 `min_trade_amount` 필드 추가 (Optional[float], 기본값: None)
- min_trade_amount가 설정된 경우, 부분 체결 시 이 값 이하로 체결되지 않도록 검증
- 최소 단위 미만 잔여 수량 처리 로직 추가

## Impact
- **Breaking Changes**: 없음 (기본값 None으로 하위 호환성 유지)
- **Affected specs**: `order-data-structure`
- **Affected code**: `packages/financial-assets/financial_assets/order/spot_order.py`
- **Migration Required**: 기존 코드는 수정 불필요. 새로운 시뮬레이션 코드에서 선택적으로 사용 가능

## Benefits
- 실제 거래소 제약을 시뮬레이션에 반영하여 정확도 향상
- 비현실적인 소수점 체결 방지
- 주문 분할 시 최소 단위 기반 검증 가능
- 백테스팅 결과의 신뢰성 증가
