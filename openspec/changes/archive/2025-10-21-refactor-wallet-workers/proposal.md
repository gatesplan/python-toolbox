# Proposal: refactor-wallet-workers

## Overview
단일 `worker.py` 파일에 있는 wallet worker 클래스들을 `workers/` 디렉토리 아래 개별 파일로 재구성하여 코드 구조와 유지보수성을 개선합니다.

## Motivation
현재 `financial_assets/wallet/worker.py`는 다음을 포함합니다:
- 1개의 추상 베이스 클래스 (`WalletWorker`)
- 5개의 구체적인 워커 구현체:
  - `TotalValueWorker`
  - `RealizedPnLWorker`
  - `UnrealizedPnLWorker`
  - `PositionSummaryWorker`
  - `CurrencySummaryWorker`

이로 인해 다음과 같은 문제가 발생합니다:
- 파일이 318줄로 길어서 코드 탐색이 어렵습니다
- 새로운 워커 추가 시 공유 파일을 수정해야 하여 충돌 가능성이 있습니다
- 클래스당 하나의 파일이라는 일반적인 Python 패키지 구조 패턴을 따르지 않습니다

## Proposed Changes
1. `financial_assets/wallet/workers/` 디렉토리 생성
2. 각 워커 클래스를 개별 파일로 이동:
   - `workers/wallet_worker.py` - 추상 베이스 클래스
   - `workers/total_value_worker.py`
   - `workers/realized_pnl_worker.py`
   - `workers/unrealized_pnl_worker.py`
   - `workers/position_summary_worker.py`
   - `workers/currency_summary_worker.py`
3. `workers/__init__.py` 생성하여 모든 워커 클래스 export
4. `wallet/__init__.py` 업데이트하여 새 위치에서 import
5. 기존 `worker.py` 파일 제거

## Benefits
- **유지보수성**: 각 워커가 개별 파일에 있어 코드 위치 파악 및 수정이 용이합니다
- **확장성**: 새 워커 추가 시 새 파일만 생성하면 되어 공유 파일 수정 불필요합니다
- **명확성**: 파일 구조가 클래스 구조와 일치합니다 (클래스당 파일 하나)
- **일관성**: 일반적인 Python 패키지 구조 패턴을 따릅니다

## Impact
- **Breaking Changes**: 없음 (public API 불변, `financial_assets.wallet`에서 import 여전히 가능)
- **Migration Required**: 불필요 (내부 리팩토링만)
- **Tests**: 기존 테스트 수정 없이 계속 동작

## Related Specs
- `wallet-inspector` - 이 워커들을 사용
- `wallet-data-structure` - wallet 모듈 구조

## Dependencies
없음
