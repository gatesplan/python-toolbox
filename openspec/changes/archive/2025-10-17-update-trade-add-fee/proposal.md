# Proposal: Update Trade - Add Fee Field

## Why
현재 Trade는 체결 정보를 담고 있지만 거래 수수료 정보가 없어, 실제 거래 비용을 정확히 추적하거나 수익률을 계산할 때 불완전합니다. 거래소 API나 시뮬레이션에서 발생하는 수수료를 Trade 객체에 포함시켜 완전한 거래 기록을 유지해야 합니다.

## What Changes
- Trade에 `fee: Token | None` 필드 추가 (선택적)
- Fee가 있는 경우와 없는 경우 모두 지원
- 기존 Trade 생성 코드와의 하위 호환성 유지 (default=None)
- Fee 관련 시나리오 추가 (테스트 포함)

## Impact
- Affected specs: trade-data-structure (MODIFIED)
- Affected code:
  - `financial_assets/trade/trade.py` - Trade dataclass
  - `tests/test_trade.py` - 테스트 추가
