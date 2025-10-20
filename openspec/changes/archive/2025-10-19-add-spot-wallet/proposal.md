# Proposal: add-spot-wallet

## Why
현재 financial-assets 패키지에는 거래를 표현하는 SpotTrade, 거래 내역을 기록하는 SpotLedger, 평균가가 다른 Pair들을 관리하는 PairStack이 구현되어 있습니다. 이제 실제 거래 시뮬레이션을 위한 마지막 핵심 컴포넌트인 **Wallet(지갑)** 모듈이 필요합니다.

Wallet은 Architecture 문서에서 정의된 "자산 조정 및 장부 작성" 역할을 담당하며, 다음 문제를 해결합니다:

1. **화폐 계정 관리**: USD, KRW 등 기준 화폐(quote currency) 잔액 관리
2. **자산 포지션 관리**: BTC-USD, ETH-USD 등 각 거래쌍별 PairStack 관리
3. **거래 처리**: SpotTrade를 받아서 자산 조정 (매수/매도)
4. **거래 기록**: SpotLedger를 통한 거래 내역 자동 기록
5. **현실적인 평단가 관리**: PairStack을 활용하여 매수 시점별로 평단가를 분리 관리

평단가(평균 단가)는 매수 시점에 대한 의미를 희석시키는 경향이 있어 실제 거래 행위에 의한 손익을 판단하는 데 장애가 됩니다. 이를 해결하기 위해 PairStack을 사용하여 평단가가 다르면 별도 레이어로 기록하는 방식을 채택합니다.

## What Changes

### 새로운 모듈: `financial_assets/wallet/`

#### `SpotWallet` 클래스
- **목적**: 단일 거래 계정의 자산 및 거래 내역 관리
- **주요 기능**:
  - `deposit_currency(symbol: str, amount: float)` - 화폐 입금
  - `withdraw_currency(symbol: str, amount: float)` - 화폐 출금
  - `process_trade(trade: SpotTrade)` - 거래 처리 및 자산 조정
  - `get_currency_balance(symbol: str) -> float` - 화폐 잔액 조회
  - `get_pair_stack(ticker: str) -> Optional[PairStack]` - 특정 거래쌍의 PairStack 조회
  - `get_ledger(ticker: str) -> Optional[SpotLedger]` - 특정 거래쌍의 거래 내역 조회
  - `list_currencies() -> list[str]` - 보유 화폐 목록
  - `list_tickers() -> list[str]` - 보유 자산 티커 목록

#### 내부 상태
- `_currencies: dict[str, Token]` - 화폐 계정 (symbol -> Token)
- `_pair_stacks: dict[str, PairStack]` - 자산 포지션 (ticker -> PairStack)
- `_ledgers: dict[str, SpotLedger]` - 거래 내역 (ticker -> SpotLedger)

#### 거래 처리 로직
**BUY (매수)**:
1. quote 화폐 잔액 확인 및 차감
2. PairStack에 Pair 추가 (자동 병합 또는 새 레이어)
3. SpotLedger에 거래 기록

**SELL (매도)**:
1. PairStack에서 해당 자산 분리 (FIFO - 스택 위부터)
2. quote 화폐 잔액 증가
3. SpotLedger에 거래 기록 (realized PnL 포함)

#### `WalletInspector` 클래스 (Director-Worker 패턴)
- **목적**: SpotWallet 통계 및 분석 기능 제공
- **주요 기능**:
  - `get_total_value(quote_symbol: str, current_prices: dict[str, Price]) -> float` - 총 자산 가치
  - `get_total_realized_pnl() -> float` - 총 실현 손익
  - `get_unrealized_pnl(quote_symbol: str, current_prices: dict[str, Price]) -> float` - 미실현 손익
  - `get_position_summary(quote_symbol: str, current_prices: dict[str, Price]) -> pd.DataFrame` - 포지션 요약
  - `get_currency_summary() -> pd.DataFrame` - 화폐 잔액 요약
- **참고**: 현재 가격은 `Price` 객체로 전달하며, `Price.c` (close) 필드를 현재가로 사용

#### Worker 인터페이스
- `WalletWorker` 추상 클래스: `analyze(wallet: SpotWallet) -> Any`
- 초기 구현 Worker들:
  - `TotalValueWorker` - 총 자산 가치 계산
  - `RealizedPnLWorker` - 실현 손익 계산
  - `UnrealizedPnLWorker` - 미실현 손익 계산
  - `PositionSummaryWorker` - 포지션 요약 생성
  - `CurrencySummaryWorker` - 화폐 잔액 요약 생성

### 새로운 Spec
- `wallet-data-structure`: SpotWallet의 요구사항 및 시나리오 정의
- `wallet-inspector`: WalletInspector와 Worker 인터페이스 정의

## Dependencies
- ✅ Token (기존)
- ✅ Pair (기존)
- ✅ PairStack (기존)
- ✅ SpotTrade, SpotSide (기존)
- ✅ SpotLedger, SpotLedgerEntry (기존)
- ✅ Price (기존) - WalletInspector에서 현재 가격 표현에 사용

## Success Criteria
1. SpotWallet 클래스 구현 완료
2. 화폐 입출금 기능 동작
3. BUY/SELL 거래 처리 정상 동작
4. PairStack과 SpotLedger 자동 연동
5. WalletInspector 및 Worker 인터페이스 구현 완료
6. 모든 통계 기능 (총 자산, 실현/미실현 손익, 포지션 요약) 동작
7. Director-Worker 패턴으로 확장 가능한 구조 확립
8. 포괄적인 테스트 스위트 작성 및 통과 (SpotWallet + WalletInspector)
9. 잔액 부족 등 에러 케이스 처리

## Out of Scope
- 선물(Futures) 지갑 (별도 구현 필요)
- 수수료(fee) 처리 (SpotTrade에 fee 필드 추가 후 별도 작업)
- 멀티 계정 관리 (상위 레이어에서 구현)
- API 연동 (별도 모듈)
