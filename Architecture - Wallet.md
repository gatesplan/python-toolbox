# Architecture - Wallet

## 개요

통합 자산 관리 시스템. 현물(Spot), 선물(Futures), 채권(Bond) 등 다양한 자산 유형을 통합 관리하며, 각 티커별 포지션을 단일 책임으로 분리하여 정교한 자산 추적과 손익 계산을 지원한다.

## 설계 철학

### Account의 독립성
- 각 Account는 독립적으로 운용되며, 다른 Account의 존재를 알 필요 없음
- 거래소별/전략별 인스턴스 구분: `upbit_spot`, `binance_spot`, `binance_futures`
- 운용 손익은 각 Account 내부에서 격리되어 관리

### Capital의 역할
- **집합체(Aggregator)**: Account들의 컨테이너, 통합 조회 제공
- **NOT 관여**: 각 Account의 세부 운용 의사결정에 간섭하지 않음
- **권한**: 자본 재배치(harvest 등)는 Capital의 고유 권한

### 거래 실행 분리
- **Account**: 상태 관리만 담당 (잔액, Position 보유)
- **TradingAgent**: 거래 전략 실행 및 조율 (외부 패키지)
- **APIAdapter**: 거래소 API 연동 (별도 패키지 `trading-adapters`)

## 아키텍처 구조

```
Capital (Account 집합체)
├─ MasterLedger (전체 거래 통합 기록)
├─ _accounts: dict[str, Account]
│   ├─ "upbit_spot": SpotAccount
│   │   ├─ SpotPosition(BTC-USDT)
│   │   └─ SpotPosition(ETH-USDT)
│   ├─ "binance_spot": SpotAccount
│   │   └─ SpotPosition(...)
│   └─ "binance_futures": FuturesAccount
│       └─ FuturesPosition(BTCUSDT-PERP)

[외부 시스템 - 별도 패키지]
TradingAgent (거래 전략 실행)
    ↓ 조율
Account ← → APIAdapter (거래소 API)
```

## 계층별 책임

### 1. Capital (Account 집합체)
- **책임**: Account 통합 조회, 전체 기록 관리
- **본질**: Aggregator - 각 Account의 독립 운용을 방해하지 않음
- **주요 속성**:
  ```python
  _accounts: dict[str, Account]  # account_id → Account (upbit_spot, binance_futures 등)
  _master_ledger: MasterLedger
  ```
- **주요 기능**:
  ```python
  get_account(account_id: str) → Account  # Account 조회
  get_total_balance() → dict[str, float]  # 전체 잔액 집계 (각 Account 조회 합산)
  harvest()  # 자본 재배치 (구체적 로직은 보류)
  ```
- **보류 사항**:
  - 자금 분배/재분배 메커니즘
  - harvest() 구체적 동작

### 2. MasterLedger (통합 장부)
- **책임**: 총자산 출납 기록 및 전체 포트폴리오 상황 추적
- **역할**:
  - 각 Account에서 Capital로 보고되는 기록을 수집
  - 총자산의 출납 기록
  - 전체 포트폴리오 상황 조회 기반 제공
  - 추후 시각화 전담 서브시스템이 이 데이터를 활용하여 개발 예정
- **저장 데이터 항목**:
  ```python
  timestamp       # 거래 시각
  account         # account_id
  event           # 거래 이벤트 유형
  asset_symbol    # 자산 심볼 (BTC)
  asset_diff      # 자산 변동량 (+0.5, -0.3)
  asset           # 변동 후 자산 잔액
  value_symbol    # 가치 심볼 (USDT)
  value_diff      # 가치 변동량 (-10000, +9500)
  value           # 변동 후 가치 잔액
  ```
  - **event 유형**: `buy`, `sell`, `long`, `short`, `reduce_long`, `reduce_short`, `liquidation`, `fee`
- **주요 기능**:
  ```python
  store(trade: Trade)  # 거래 기록 저장
  to_dataframe()  # DataFrame 변환
  ```

### 3. Account (상태 관리)
- **책임**: 잔액 관리, Position 보유, 거래 결과 기록
- **본질**: 수동적 상태 저장소 - 거래 의사결정 하지 않음
- **주요 속성**:
  ```python
  _balance: dict[str, float]  # 현재 보유 잔액 (symbol → amount)
  _positions: dict[str, Position]  # ticker → Position
  ```
- **주요 기능**:
  ```python
  get_balance(symbol: str) → float  # 잔액 조회
  record_trade(trade: Trade)  # 거래 결과 기록 (외부에서 수신)
  get_position(ticker: str) → Position  # Position 조회
  ```
- **자산 유형별 클래스**:
  - **SpotAccount**: 현물 보유, PairStack 기반 FIFO 정산
  - **FuturesAccount**: 마진, 청산가, 펀딩비
  - **BondAccount**: 만기, 이자
- **인스턴스 구분**: 문자열 키로 여러 인스턴스 생성 가능
  - 예: `upbit_spot`, `binance_spot`, `binance_futures`

### 4. Position (티커별 포지션)
- **책임**: 단일 티커의 거래/포지션 관리 (단일 책임 원칙)
- **SpotPosition**:
  ```python
  _ticker: str
  _pair_stack: PairStack  # FIFO
  _ledger: Ledger
  ```
- **FuturesPosition**:
  ```python
  _ticker: str
  _side: PositionSide  # LONG / SHORT
  _quantity: float
  _entry_price: float
  _liquidation_price: float
  _ledger: Ledger
  ```

## 설계 원칙

### 1. 계층 분리
- Spot과 Futures는 본질이 다름
- Account 타입 계층에서 분리하여 관리

### 2. 단일 책임
- Position은 하나의 티커만 관리
- Account는 상태 관리만 담당
- 거래 의사결정은 외부 TradingAgent

### 3. 확장성
- 새로운 자산 유형: Account 클래스 추가
- 새로운 거래소: Account 인스턴스 추가
- 새로운 전략: TradingAgent 구현

## 외부 시스템 (별도 패키지)

### TradingAgent (미구현)
- **패키지**: 별도 독립
- **책임**: 거래 전략 실행, Account/APIAdapter 조율
- **역할**:
  - Account 상태 조회
  - 거래 의사결정
  - APIAdapter를 통한 주문 실행
  - 체결 결과를 Account에 반영

### APIAdapter (미구현)
- **패키지**: `trading-adapters` (별도)
- **책임**: 거래소 API 연동
- **구현체**:
  - BinanceAdapter
  - UpbitAdapter
  - SimulatorAdapter (테스트용)

## 자금 관리

### Account 독립 운용
- 각 Account는 초기 할당받은 잔액을 직접 보유
- 거래로 인한 손익은 Account 내부에서만 변동
- 다른 Account에 영향 없음 (완전 격리)

### 거래 흐름 (TradingAgent 조율)
```
[매수]
TradingAgent
  ↓ 1. 잔액 확인
Account.get_balance()
  ↓ 2. 거래 실행
APIAdapter.place_order()
  ↓ 3. 체결 결과
TradingAgent
  ↓ 4. 상태 업데이트
Account.record_trade()
  ↓ 5. Pair 저장
Position._pair_stack.append(pair)
  ↓ 6. 기록
Capital.MasterLedger.store()

[매도]
TradingAgent
  ↓ 1. Position 조회
Account.get_position()
  ↓ 2. Pair 분할/제거
Position._pair_stack.split()
  ↓ 3. 거래 실행
APIAdapter.place_order()
  ↓ 4. 잔액 증가
Account.record_trade()
  ↓ 5. 기록
Capital.MasterLedger.store()
```

### 제약사항
- Position은 직접 자금 보유 안함 (Account 잔액 참조)
- 모든 거래 기록은 MasterLedger에 저장
- 거래 의사결정은 외부 TradingAgent 책임

### 보류 사항
- Capital ↔ Account 간 자금 재분배 메커니즘
- harvest() 동작 방식
