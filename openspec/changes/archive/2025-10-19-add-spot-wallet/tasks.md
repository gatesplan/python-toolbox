# Implementation Tasks

## 1. 모듈 구조 생성
- [x] 1.1 `financial_assets/wallet/` 디렉토리 생성
- [x] 1.2 `financial_assets/wallet/__init__.py` 생성 및 exports 정의
- [x] 1.3 패키지 구조 문서 업데이트 (필요 시)

## 2. SpotWallet 클래스 구현
- [x] 2.1 `financial_assets/wallet/spot_wallet.py` 파일 생성
- [x] 2.2 `SpotWallet` 클래스 정의 및 내부 상태 설계:
  - `_currencies: dict[str, Token]` - 화폐 계정
  - `_pair_stacks: dict[str, PairStack]` - 자산 포지션
  - `_ledgers: dict[str, SpotLedger]` - 거래 내역
- [x] 2.3 `__init__()` 메서드 구현
- [x] 2.4 화폐 관리 메서드 구현:
  - `deposit_currency(symbol: str, amount: float)`
  - `withdraw_currency(symbol: str, amount: float)`
  - `get_currency_balance(symbol: str) -> float`
- [x] 2.5 조회 메서드 구현:
  - `get_pair_stack(ticker: str) -> Optional[PairStack]`
  - `get_ledger(ticker: str) -> Optional[SpotLedger]`
  - `list_currencies() -> list[str]`
  - `list_tickers() -> list[str]`
- [x] 2.6 BUY 거래 처리 로직 구현 (`_process_buy_trade`)
- [x] 2.7 SELL 거래 처리 로직 구현 (`_process_sell_trade`)
- [x] 2.8 `process_trade(trade: SpotTrade)` 메서드 구현 (BUY/SELL 분기)
- [x] 2.9 Docstring 및 예제 추가
- [x] 2.10 `__str__` 및 `__repr__` 메서드 구현

## 3. WalletWorker 인터페이스 및 Worker 구현
- [x] 3.1 `financial_assets/wallet/worker.py` 파일 생성
- [x] 3.2 `WalletWorker` 추상 클래스 정의 (`analyze` 메서드)
- [x] 3.3 `TotalValueWorker` 구현 - 총 자산 가치 계산
- [x] 3.4 `RealizedPnLWorker` 구현 - 실현 손익 계산
- [x] 3.5 `UnrealizedPnLWorker` 구현 - 미실현 손익 계산
- [x] 3.6 `PositionSummaryWorker` 구현 - 포지션 요약 DataFrame
- [x] 3.7 `CurrencySummaryWorker` 구현 - 화폐 잔액 요약 DataFrame
- [x] 3.8 Docstring 및 예제 추가

## 4. WalletInspector 클래스 구현
- [x] 4.1 `financial_assets/wallet/wallet_inspector.py` 파일 생성
- [x] 4.2 `WalletInspector` 클래스 정의 및 초기화
- [x] 4.3 `get_total_value()` 메서드 구현 (TotalValueWorker 사용)
- [x] 4.4 `get_total_realized_pnl()` 메서드 구현 (RealizedPnLWorker 사용)
- [x] 4.5 `get_unrealized_pnl()` 메서드 구현 (UnrealizedPnLWorker 사용)
- [x] 4.6 `get_position_summary()` 메서드 구현 (PositionSummaryWorker 사용)
- [x] 4.7 `get_currency_summary()` 메서드 구현 (CurrencySummaryWorker 사용)
- [x] 4.8 Docstring 및 예제 추가
- [x] 4.9 `__str__` 및 `__repr__` 메서드 구현
- [x] 4.10 `__init__.py`에 WalletInspector 및 WalletWorker export 추가

## 5. 테스트 작성 - SpotWallet
- [x] 5.1 `tests/test_spot_wallet.py` 파일 생성
- [x] 5.2 SpotWallet 초기화 테스트
- [x] 5.3 화폐 입금 테스트
- [x] 5.4 화폐 출금 테스트
- [x] 5.5 잔액 부족 시 출금 실패 테스트
- [x] 5.6 없는 화폐 조회 테스트 (0 반환)
- [x] 5.7 BUY 거래 처리 테스트
- [x] 5.8 잔액 부족으로 BUY 실패 테스트
- [x] 5.9 여러 번 BUY - PairStack 레이어 관리 테스트
- [x] 5.10 SELL 거래 처리 테스트
- [x] 5.11 자산 부족으로 SELL 실패 테스트
- [x] 5.12 전체 포지션 청산 테스트
- [x] 5.13 화폐 목록 조회 테스트
- [x] 5.14 티커 목록 조회 테스트
- [x] 5.15 존재하지 않는 PairStack/Ledger 조회 테스트
- [x] 5.16 문자열 표현 테스트
- [x] 5.17 복잡한 시나리오 테스트 (여러 거래쌍, 반복 매수/매도)

## 6. 테스트 작성 - WalletInspector
- [x] 6.1 `tests/test_wallet_inspector.py` 파일 생성
- [x] 6.2 WalletInspector 초기화 테스트
- [x] 6.3 총 자산 가치 계산 테스트 (화폐만)
- [x] 6.4 총 자산 가치 계산 테스트 (자산 포함)
- [x] 6.5 여러 자산 총 가치 계산 테스트
- [x] 6.6 총 실현 손익 조회 테스트
- [x] 6.7 여러 거래쌍 실현 손익 합계 테스트
- [x] 6.8 미실현 손익 조회 테스트
- [x] 6.9 여러 자산 미실현 손익 테스트
- [x] 6.10 포지션 요약 DataFrame 테스트
- [x] 6.11 화폐 잔액 요약 DataFrame 테스트
- [x] 6.12 Custom Worker 확장 테스트
- [x] 6.13 문자열 표현 테스트

## 7. 검증
- [x] 7.1 SpotWallet 테스트 실행: `pytest packages/financial-assets/tests/test_spot_wallet.py -v`
- [x] 7.2 WalletInspector 테스트 실행: `pytest packages/financial-assets/tests/test_wallet_inspector.py -v`
- [x] 7.3 전체 wallet 모듈 테스트 커버리지 확인
- [x] 7.4 PairStack 및 SpotLedger와의 통합 검증
- [x] 7.5 Worker 패턴 확장 가능성 검증
- [x] 7.6 에러 케이스 처리 검증 (잔액 부족, 자산 부족 등)
- [x] 7.7 패키지 exports 업데이트 확인

## 8. 문서화 (선택)
- [x] 8.1 Architecture 문서 업데이트 (Wallet 구현 완료 표시)
- [x] 8.2 사용 예제 작성 (선택)
- [x] 8.3 Director-Worker 패턴 문서 작성 (선택)
