# Proposal: add-order-module

## Summary
Order 모듈을 추가하여 거래 주문(미체결 상태)을 표현하고 부분/전체 체결을 처리하는 기능을 제공합니다. Order는 단일 마켓 시뮬레이션의 핵심 빌딩블록으로, 지정가/시장가 거래 흐름에서 주문 상태를 추적하고 Trade 객체를 생성하는 팩토리 역할을 합니다.

## Motivation
현재 financial-assets 패키지는 Trade(체결 완료된 거래)를 표현하는 구조는 있으나, Order(미체결 주문) 개념이 없습니다. Trading Sim 아키텍처에서 정의한 거래 처리 흐름을 구현하려면:

1. **지정가 거래**: Order 객체를 주문장에 등록하고 체결 조건 만족 시 Trade로 변환
2. **시장가 거래**: Order를 거치지 않고 즉시 Trade 생성
3. **부분 체결**: 주문의 일부만 체결되고 나머지는 미체결 상태 유지

Order 모듈은 이러한 시나리오를 지원하기 위한 필수 데이터 구조입니다.

## Goals
- Order 데이터 클래스 구현 (가변 객체)
- 부분 체결 처리: `fill_by_asset_amount()`, `fill_by_value_amount()` 메서드로 Trade 생성
- 미체결 수량 조회: `remaining_asset()`, `remaining_value()`, `remaining_rate()` 제공
- 주문 상태 관리: pending, partial, filled, canceled
- 기존 모듈(Token, Pair, StockAddress, Trade, TradeSide) 재사용

## Non-Goals
- OrderBook 구현 (별도 change로 분리)
- API/시뮬레이터 구현 (별도 change로 분리)
- Wallet 구현 (별도 change로 분리)
- Stop order 로직 구현 (기본 데이터 구조만 제공)

## Scope
**New Capability**: `order-data-structure`
- Order 클래스
- OrderStatus Enum (또는 문자열 상수)
- fill 메서드를 통한 Trade 팩토리 기능
- 상태 관리 메서드

## Dependencies
- `token` (기존)
- `pair` (기존)
- `stock_address` (기존)
- `trade` (기존)

## Rollout Plan
1. `financial_assets/order/` 폴더 생성
2. `order.py` 구현
3. 테스트 작성
4. `__init__.py` 업데이트하여 public API 노출

## Testing Strategy
- 주문 생성 테스트 (market, limit, stop)
- 부분 체결 테스트 (asset/value 기준)
- 전체 체결 테스트
- 미체결 수량 계산 테스트
- 상태 전이 테스트 (pending → partial → filled)
- 주문 취소 테스트
- Trade 객체 생성 검증

## Risks
- **설계 변경 가능성**: 실제 OrderBook/Wallet 구현 시 인터페이스 조정 필요할 수 있음
- **완화 방안**: Trade 모듈과 유사한 불변성 원칙 유지, 명확한 책임 분리

## Open Questions
None - 설계가 명확하게 정의되었음
