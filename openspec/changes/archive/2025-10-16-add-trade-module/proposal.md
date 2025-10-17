# Proposal: Add Trade Module

## Summary
체결 완료된 거래의 기록을 표현하는 Trade 데이터 구조를 financial-assets 패키지에 추가합니다. Trade는 거래 시뮬레이션이나 실제 거래 API 응답을 표준화된 형식으로 캡슐화하여 시스템 간 데이터 전송 및 기록 저장을 지원합니다.

## Motivation
현재 financial-assets는 Token, Pair 등 거래 자산을 표현하는 구조는 있지만, 체결된 거래 자체를 표현하는 데이터 구조가 없습니다. 거래 시뮬레이션이나 실제 거래소 API에서 반환되는 체결 정보를 일관된 형식으로 처리하고, 다른 컴포넌트로 전달하거나 저장하기 위해 표준화된 Trade 객체가 필요합니다.

## Scope

### In Scope
- Trade 데이터 클래스 구현 (불변 객체)
- TradeSide enum 정의 (BUY, SELL, LONG, SHORT)
- 기존 모듈(Token, Pair, StockAddress) 통합
- 기본적인 문자열 표현 메서드
- 단위 테스트

### Out of Scope
- 거래 실행 로직 (Order 관련 기능)
- 거래 이력 관리 및 집계
- 거래 데이터 영속화 (저장/로드)
- 거래 검증 또는 유효성 검사

## Dependencies
- 기존 모듈: Token, Pair, StockAddress
- 새 의존성 없음

## Risks
- None (단순 데이터 구조 추가)

## Alternatives Considered
- dataclass 대신 일반 클래스 사용: dataclass가 불변성과 자동 생성 메서드를 제공하여 더 적합
- Pair 대신 별도 필드로 수량/가격 저장: Pair를 재사용하면 기존 API와 일관성 유지
