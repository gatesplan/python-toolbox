# Design: Unified Ledger System

## Context

현재 시스템은 ticker별로 SpotLedger를 분리하여 BUY/SELL 거래만 기록합니다. 하지만 화폐 입출금, 자산 입출금, 수수료 등은 특정 ticker에 속하지 않거나 ticker를 넘나드는 작업이므로 기존 구조로는 기록할 수 없습니다.

레거시 시스템(ff-wallet)은 WalletTransaction으로 모든 지갑 작업을 기록했지만, 이는 ticker별 거래 분석(평균가, 실현손익)과 별도로 관리되어 중복과 복잡도를 야기했습니다.

## Goals / Non-Goals

**Goals:**
- 모든 지갑 작업(입금, 출금, 거래, 수수료)을 단일 ledger 구조로 통합
- Account 기반 ledger로 화폐("USDT") 및 ticker("BTC-USDT") 모두 기록 가능
- 거래 현상의 본질(asset/value 변동)만 기록하여 단순성 유지
- 기존 SpotLedger의 평균가/실현손익 계산 로직 보존

**Non-Goals:**
- 복식부기나 복잡한 회계 시스템 도입
- Active/Pending 자산 구분은 Wallet의 책임 (ledger는 최종 결과만 기록)
- Promise/Resolve 패턴 완전 구현 (이번 변경에서는 기반만 마련)

## Decisions

### Decision 1: Account-based Ledger

**What:** 각 account(화폐 심볼 또는 ticker)마다 별도 Ledger 인스턴스 생성

**Why:**
- 화폐 계정("USDT")과 자산 계정("BTC-USDT")을 동일한 구조로 관리
- Ticker별 분석(평균가, 손익)은 해당 ledger에서 독립적으로 계산 가능
- 단일 책임 원칙 유지: 각 ledger는 하나의 계정만 추적

**Alternatives considered:**
- 통합 WalletLedger: 모든 계정을 하나의 ledger에 기록 → 복잡도 증가, 계정별 분석 어려움
- 화폐/자산 ledger 분리: CurrencyLedger와 SpotLedger 병행 → 중복, 일관성 문제

### Decision 2: Explicit Methods for Different Operations

**What:** `add_currency_deposit`, `add_currency_withdraw`, `add_asset_deposit`, `add_asset_withdraw` 등 명시적 메서드 제공

**Why:**
- 호출 지점에서 의도가 명확 (currency vs asset)
- asset_change=0 또는 value_change=0 계산을 메서드 내부에서 처리
- 실수로 잘못된 변동 기록 방지

**Alternatives considered:**
- 단일 `add_entry()` 메서드: 호출자가 asset_change/value_change 계산 → 오류 가능성 높음
- Event 타입만으로 구분: DEPOSIT 이벤트가 asset인지 value인지 불명확

### Decision 3: EventType without Asset/Value Distinction

**What:** EventType은 DEPOSIT, WITHDRAW, BUY, SELL, FEE로 단순화 (DEPOSIT_ASSET, DEPOSIT_VALUE 등으로 세분화하지 않음)

**Why:**
- asset_change/value_change 컬럼이 이미 구분 제공 (0이면 해당 없음)
- 이벤트 타입은 "무슨 작업"인지만 표현, "무엇이 변동했는지"는 change 컬럼이 담당
- 더 단순하고 직관적

### Decision 4: Cumulative Tracking in Ledger

**What:** Ledger가 _cumulative_asset, _cumulative_value를 내부 상태로 유지

**Why:**
- 매 entry마다 누적량 계산 자동화
- DataFrame에서 시간에 따른 잔액 변화 추적 용이
- Wallet의 실제 잔액과 독립적으로 검증 가능 (감사 추적)

**Alternatives considered:**
- Entry만 저장하고 누적은 분석 시 계산: 반복 계산 필요, 비효율적

## Risks / Trade-offs

**Risk 1: Breaking Change**
- 기존 SpotLedger API 사용 코드 모두 수정 필요
- **Mitigation:** 기존 SpotLedger를 deprecated로 유지하고 점진적 마이그레이션 지원

**Risk 2: 평균가/실현손익 계산 누락**
- 새 Ledger는 asset/value만 기록하고 평균가는 별도 계산 필요
- **Mitigation:** add_trade() 메서드에서 기존 SpotLedger 로직 재사용하여 평균가 추적 (내부 상태로 유지 가능)

**Trade-off: 단순성 vs 기능성**
- Promise/Resolve를 ledger에 기록하지 않음 → 예약 작업 추적 불가
- **Rationale:** Ledger는 최종 결과만 기록. 예약은 Wallet의 내부 상태이며 거래 체결 시점에만 ledger에 기록

## Migration Plan

1. **Phase 1: 새 Ledger 구현**
   - LedgerEntry, EventType, Ledger 클래스 구현
   - 기존 SpotLedger와 병행 사용 가능하도록 별도 모듈로 구현

2. **Phase 2: SpotWallet 통합**
   - SpotWallet에 새 Ledger 통합
   - deposit_currency, withdraw_currency에 ledger 기록 추가
   - process_trade에 BUY/SELL/FEE 기록 추가

3. **Phase 3: 테스트 및 검증**
   - 전체 테스트 스위트 실행
   - 기존 기능 회귀 없음 확인

4. **Phase 4: 문서화 및 Deprecation**
   - 새 API 문서화
   - 기존 SpotLedger deprecation 경고 추가 (필요시)

**Rollback:** 새 Ledger는 선택적으로 활성화 가능하도록 하여, 문제 발생 시 기존 SpotLedger로 즉시 전환 가능

## Open Questions

1. **평균가 추적 방식:**
   - Option A: Ledger 내부에 _average_price 상태 유지 (기존 SpotLedger 방식)
   - Option B: Entry에 average_price 기록하되 Ledger는 계산만 수행
   - **결정 필요:** 구현 시점에 사용성과 일관성 고려하여 선택

2. **DataFrame 출력 형식:**
   - 모든 컬럼을 평면화? (timestamp, account, event, asset_change, ...)
   - 또는 중첩 구조? (metadata 컬럼 추가?)
   - **결정 필요:** 기존 to_dataframe() 사용 패턴 확인 후 결정

3. **수수료 처리:**
   - 별도 FEE entry로 기록? (현재 계획)
   - 아니면 BUY/SELL entry에 fee_amount 필드 추가?
   - **결정 필요:** 분석 시 편의성 고려하여 최종 결정
