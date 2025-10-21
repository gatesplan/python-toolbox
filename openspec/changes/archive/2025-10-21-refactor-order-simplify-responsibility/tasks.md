# Implementation Tasks

## 1. SpotOrder 클래스 수정
- [x] 1.1 `__init__` 시그니처에 `filled_amount=0.0`, `status="pending"`, `fee_rate=0.0` 파라미터 추가
- [x] 1.2 내부 헬퍼 메서드 `_clone(**overrides)` 구현
  - 모든 필드를 복제하고 일부만 오버라이드하는 헬퍼
  - fee_rate 필드 포함
  - 불변 복제 패턴의 중복 코드 제거
- [x] 1.3 `fill_by_asset_amount(amount)` 메서드 수정
  - 시그니처 변경: `(amount, price, timestamp) -> SpotTrade` → `(amount) -> SpotOrder`
  - SpotTrade 생성 로직 제거
  - 불변 복제 패턴 적용: 원본 유지 + 새 SpotOrder 반환
  - filled_amount 누적 계산
  - 상태 자동 판단 (pending/partial/filled)
- [x] 1.4 `fill_by_value_amount(value_amount)` 메서드 수정
  - 시그니처 변경: `(amount, price, timestamp) -> SpotTrade` → `(amount) -> SpotOrder`
  - value를 asset으로 변환 후 `fill_by_asset_amount()` 호출
  - 시장가 주문(price=None) 및 0 가격 오류 처리 유지
- [x] 1.5 `to_pending_state() -> SpotOrder` 메서드 추가
  - status="pending"로 복제
- [x] 1.6 `to_partial_state() -> SpotOrder` 메서드 추가
  - status="partial"로 복제
- [x] 1.7 `to_filled_state() -> SpotOrder` 메서드 추가
  - status="filled"로 복제
- [x] 1.8 `to_canceled_state() -> SpotOrder` 메서드 추가
  - status="canceled"로 복제
- [x] 1.9 `cancel()` 메서드 제거
- [x] 1.10 `_validate_fill()` 메서드 유지 (검증 로직 필요)
- [x] 1.11 `is_filled()`, `remaining_asset()`, `remaining_value()`, `remaining_rate()` 메서드 유지 (변경 없음)

## 2. 테스트 업데이트
- [x] 2.1 `test_order.py` - fill 메서드 반환 타입 변경 테스트
  - TestFillByAssetAmount: SpotTrade 반환 검증 제거, SpotOrder 반환 검증 추가
  - TestFillByValueAmount: 동일하게 수정
  - 기존 trade 객체 검증 로직 제거
- [x] 2.2 불변성 테스트 추가
  - fill 메서드 호출 후 원본 order가 변경되지 않음 검증
  - 여러 번 체결 체이닝 테스트
- [x] 2.3 상태 변경 메서드 테스트 추가
  - `to_pending_state()` 테스트
  - `to_partial_state()` 테스트
  - `to_filled_state()` 테스트
  - `to_canceled_state()` 테스트
  - 모두 원본 불변 검증 포함
- [x] 2.4 fee_rate 필드 테스트 추가
  - fee_rate 기본값 0.0 검증
  - fee_rate 설정 및 복제 검증
  - 외부에서 fee_rate를 사용한 fee 계산 예제 테스트
- [x] 2.5 상태 자동 판단 테스트
  - fill_by_asset_amount로 부분 체결 시 "partial" 자동 설정 검증
  - fill_by_asset_amount로 전체 체결 시 "filled" 자동 설정 검증
- [x] 2.6 cancel() 관련 테스트 제거
  - TestSpotOrderStatus.test_cancel_order → test_to_canceled_state로 변경
  - TestSpotOrderStatus.test_cannot_fill_canceled_order 수정 (to_canceled_state 사용)
- [x] 2.7 TradeFactory 테스트 제거
  - TestTradeFactory 클래스 전체 제거 (SpotTrade 생성은 외부 책임)
- [x] 2.8 모든 테스트 실행 및 통과 확인

## 3. 문서 업데이트
- [x] 3.1 `spot_order.py` 모듈 docstring 업데이트
  - "SpotTrade 객체를 생성하는 팩토리 역할" 언급 제거
  - "불변 복제 패턴을 통한 상태 관리" 언급 추가
- [x] 3.2 `SpotOrder` 클래스 docstring 업데이트
  - "가변 데이터 구조" → "데이터 표현 구조 (불변 업데이트 지원)"
  - 사용 예시를 불변 복제 패턴으로 변경
  - SpotTrade 생성 예시는 외부 코드로 분리
- [x] 3.3 `fill_by_asset_amount()` docstring 업데이트
  - 반환 타입: SpotTrade → SpotOrder
  - 파라미터: price, timestamp 제거
  - 불변 복제 패턴 설명 추가
  - 예제 코드 업데이트
- [x] 3.4 `fill_by_value_amount()` docstring 업데이트
  - 동일하게 수정
- [x] 3.5 새 메서드 docstring 작성
  - `_clone()`: 내부 헬퍼 메서드 설명
  - `to_pending_state()`, `to_partial_state()`, `to_filled_state()`, `to_canceled_state()`: 각각 작성
- [x] 3.6 fee_rate 필드 문서화
  - 필드 설명: 거래 수수료 비율 (0.001 = 0.1%)
  - fee 계산 예제 추가 (BUY/SELL 구분)
- [x] 3.7 Examples 섹션 업데이트
  - 불변 복제 패턴 예제
  - 외부에서 SpotTrade 생성하는 예제 추가 (fee_rate 사용)

## 4. 검증
- [x] 4.1 모든 단위 테스트 통과 (29 tests passed)
- [x] 4.2 불변성 검증 (원본 order가 변경되지 않음)
