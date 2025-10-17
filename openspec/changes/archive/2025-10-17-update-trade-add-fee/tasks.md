# Tasks: Update Trade - Add Fee Field

## Implementation Tasks

1. **Trade 클래스에 fee 필드 추가** ✓
   - [x] `financial_assets/trade/trade.py` 수정
   - [x] `fee: Token | None = None` 필드 추가
   - [x] docstring 업데이트 (fee 설명 추가)
   - [x] Validation: fee 필드 접근 테스트

2. **문자열 표현 메서드 업데이트** ✓
   - [x] `__repr__` 메서드에 fee 포함
   - [x] `__str__` 메서드는 간결성 유지 (fee 제외)
   - [x] Validation: 문자열 출력 확인

3. **테스트 업데이트** ✓
   - [x] `tests/test_trade.py` 수정
   - [x] Fee가 있는 Trade 생성 테스트
   - [x] Fee가 없는 Trade 생성 테스트 (default None)
   - [x] Fee Token의 symbol과 amount 접근 테스트
   - [x] Validation: 모든 테스트 통과

4. **하위 호환성 검증** ✓
   - [x] 기존 테스트가 fee 없이도 동작하는지 확인
   - [x] fee 파라미터를 명시하지 않은 경우 None인지 확인
   - [x] Validation: 기존 코드 영향 없음

## Testing Strategy
- Fee가 있는 경우: Token 객체로 fee 전달, 접근 가능
- Fee가 없는 경우: fee=None (default), None 확인
- 하위 호환성: 기존 Trade(...) 호출이 그대로 동작
- 불변성: fee 포함해도 frozen dataclass 유지

## Definition of Done
- [x] Trade에 fee: Token | None 필드 추가
- [x] Docstring 업데이트
- [x] __repr__ 메서드 업데이트
- [x] 테스트 추가 (fee 있음/없음)
- [x] 모든 테스트 통과
- [x] 하위 호환성 확인
