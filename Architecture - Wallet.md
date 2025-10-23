# Architecture - Wallet

## 개요

통합 자산 관리 시스템. 현물(Spot), 선물(Futures), 채권(Bond) 등 다양한 자산 유형을 통합 관리하며, 각 티커별 포지션을 단일 책임으로 분리하여 정교한 자산 추적과 손익 계산을 지원한다.

## 아키텍처 구조

```
Capital (최상위 자산 관리)
├─ MasterLedger (전체 거래 통합 기록)
├─ SpotAccount (현물 계정)
│   ├─ SpotPosition(BTC-USDT)
│   ├─ SpotPosition(ETH-USDT)
│   └─ SpotPosition(...)
├─ FuturesAccount (선물 계정)
│   ├─ FuturesPosition(BTCUSDT-PERP)
│   └─ FuturesPosition(...)
└─ BondAccount (채권 계정)
    └─ ...
```

## 계층별 책임

### 1. Capital (최상위)
- **책임**: 전체 자산 통합 관리 및 비율 기반 할당
- **주요 속성**:
  ```python
  _total_balance: dict[str, float]  # 총 보유 자금
  _accounts: dict[str, Account]  # account_id → Account
  _allocation_ratios: dict[str, float]  # account_id → 비율 (0.0~1.0)
  _master_ledger: MasterLedger
  ```
- **주요 기능**:
  ```python
  deposit(token: Token)  # 총 자금 입금
  withdraw(token: Token)  # 총 자금 출금
  harvest()  # 각 계정의 자산을 일정 비율로 정리하고 현금화 (목표 설정 엔트리포인트)
  ```

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

### 3. Account (자산 유형별 계정)
- **책임**: 자산 유형별 관리 및 자금 중개
- **주요 속성**:
  ```python
  _used: dict[str, float]  # 현재 사용 중인 금액
  _positions: dict[str, Position]  # ticker → Position
  _capital: Capital  # 상위 참조
  ```
- **자산 유형별**:
  - **SpotAccount**: 현물 보유, FIFO 정산
  - **FuturesAccount**: 마진, 청산가, 펀딩비
  - **BondAccount**: 만기, 이자

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
- Account 계층에서 분리하여 관리

### 2. 단일 책임
- Position은 하나의 티커만 관리
- 상위 계층에서 통합/분배

### 3. 확장성
- 새로운 자산 유형 추가 시 Account만 추가

## 자금 관리

### 비율 기반 사전 할당
- Capital이 총 자금 보유
- 각 Account에 비율(0.0~1.0)로 할당
- 실제 할당 금액은 런타임에 계산: `총액 * 비율`

### 자금 흐름
```
Position → Account 자금 요청
  ↓
Account 가용 자금 확인 (allocated - used)
  ↓ 충분: 승인 / 부족: 거부
  ↓
Account 자금 인출 (used 증가)
  ↓
Capital에 보고
  ↓
MasterLedger 기록
```

### 제약사항
- Account는 할당량 초과 불가
- Position은 직접 자금 보유 안함 (Account 중개)
- 모든 자금 이동은 MasterLedger에 기록
