# Unify Ledger System

## Why

현재 SpotLedger는 거래(trade)만 기록하고 화폐 입출금, 자산 입출금 등의 지갑 작업을 기록하지 못합니다. 이로 인해 전체 지갑 활동 히스토리를 추적할 수 없으며, 디버깅과 감사 추적이 어렵습니다. 또한 레거시 구현의 Promise/Resolve 패턴(자산 예약)이 없어 주문 대기 상태에서 자산이 중복 사용되는 문제가 발생할 수 있습니다.

## What Changes

- **통합 Ledger 시스템**: 거래뿐만 아니라 모든 지갑 작업(입금, 출금, 거래, 수수료)을 단일 ledger에 기록
- **EventType 확장**: DEPOSIT, WITHDRAW, BUY, SELL, FEE 이벤트 타입으로 모든 자산 변동 추적
- **명시적 API**: `add_currency_deposit`, `add_currency_withdraw`, `add_asset_deposit`, `add_asset_withdraw` 등 명시적 메서드 제공
- **누적 추적**: asset/value의 변동량(change)과 변동 후 누적량을 모두 기록
- **Promise/Resolve 패턴 추가** (향후 확장): 자산 예약 시스템 도입을 위한 기반 마련

## Impact

- Affected specs: `ledger-data-structure` (new), `spot-ledger-data-structure` (replaced), `wallet-data-structure` (modified)
- Affected code:
  - `financial_assets/ledger/ledger_entry.py` (new)
  - `financial_assets/ledger/ledger.py` (new)
  - `financial_assets/ledger/spot_ledger.py` (deprecated or refactored)
  - `financial_assets/wallet/spot_wallet.py` (modified to integrate)
- **BREAKING**: SpotLedger API가 변경되며, 기존 코드는 새로운 Ledger API로 마이그레이션 필요
