# Financial-Assets Futures Trading Roadmap

## 현재 구현 상태 (Spot 거래)

### 핵심 컴포넌트

1. **StockAddress**: 거래소/심볼 주소 체계
2. **Token/Pair/PairStack**: 자산 표현 및 FIFO 포지션 관리
3. **SpotOrder**: 불변 패턴 기반 주문, 부분 체결 지원
4. **SpotTrade**: 불변 거래 기록
5. **SpotWallet**: 화폐 계정 + 포지션(PairStack) + 거래 처리
6. **SpotLedger**: 평균 진입가 및 실현 손익 자동 계산

### 아키텍처 특징

- 불변성 중심 설계
- FIFO 포지션 관리
- 레이어 분리 (데이터/로직/계산)

---

## Spot vs Futures 핵심 차이점

| 항목 | Spot | Futures |
|------|------|---------|
| **자산 교환** | 즉시 교환 | 계약 거래 |
| **레버리지** | 없음 (1x) | 1x ~ 125x |
| **증거금** | 전액 필요 | 일부만 필요 (Initial/Maintenance) |
| **포지션** | BUY/SELL 단순 | LONG/SHORT 양방향, 진입/청산 개념 |
| **청산** | 없음 | 증거금률 미달 시 강제 청산 |
| **손익** | 실현만 | 실현 + 미실현 (마크가격 기준) |
| **수수료** | 거래 수수료만 | 거래 수수료 + 자금 조달 수수료 |
| **평균가** | FIFO 레이어별 | 단일 평균 진입가 |

---

## 구현 계획

### Phase 1: 기본 인프라 (필수)

다른 모든 기능의 기반이 되는 핵심 데이터 구조입니다.

#### 1. FuturesSide (열거형)

```python
from enum import Enum

class FuturesSide(Enum):
    LONG_ENTRY = "long_entry"    # Long 포지션 진입
    LONG_EXIT = "long_exit"       # Long 포지션 청산
    SHORT_ENTRY = "short_entry"   # Short 포지션 진입
    SHORT_EXIT = "short_exit"     # Short 포지션 청산
```

#### 2. FuturesPosition (클래스)

포지션 상태 및 계산 책임

```python
@dataclass
class FuturesPosition:
    side: Literal["LONG", "SHORT"]
    entry_price: float           # 평균 진입가
    quantity: float              # 포지션 수량
    leverage: int                # 레버리지 배수
    initial_margin: float        # 초기 증거금
    maintenance_margin: float    # 유지 증거금

    def unrealized_pnl(self, mark_price: float) -> float:
        """미실현 손익 계산"""

    def liquidation_price(self) -> float:
        """청산 가격 계산"""

    def margin_ratio(self, mark_price: float) -> float:
        """증거금 비율 계산"""
```

#### 3. FuturesTrade (불변 데이터)

체결된 선물 거래 기록

```python
@dataclass(frozen=True)
class FuturesTrade:
    stock_address: StockAddress
    trade_id: str
    fill_id: str
    side: FuturesSide
    pair: Pair
    leverage: int
    is_reduce_only: bool
    timestamp: int
    fee: Optional[Token] = None
```

#### 4. FuturesOrder (불변 복제 패턴)

선물 주문 데이터 및 상태 관리

```python
class FuturesOrder:
    order_id: str
    stock_address: StockAddress
    side: FuturesSide
    order_type: str  # "limit", "market", "stop"
    price: Optional[float]
    amount: float
    leverage: int
    reduce_only: bool
    take_profit_price: Optional[float]
    stop_loss_price: Optional[float]
    filled_amount: float
    status: str
    timestamp: int
    fee_rate: float

    def fill_by_asset_amount(self, amount: float) -> FuturesOrder:
        """불변 복제 패턴으로 체결 상태 업데이트"""
```

---

### Phase 2: 핵심 기능

실제 거래 시뮬레이션에 필요한 핵심 로직입니다.

#### 5. FuturesWallet (핵심)

증거금 관리 및 포지션 처리

```python
class FuturesWallet:
    _margin_balance: float
    _positions: dict[str, FuturesPosition]
    _ledgers: dict[str, FuturesLedger]

    def deposit_margin(self, amount: float) -> None:
        """증거금 입금"""

    def withdraw_margin(self, amount: float) -> None:
        """증거금 출금 (가용 증거금 확인 필요)"""

    def process_trade(self, trade: FuturesTrade) -> None:
        """거래 처리: 포지션 진입/증빙/청산"""

    def check_liquidation(self, mark_prices: dict[str, float]) -> list[str]:
        """청산 대상 티커 반환"""

    def execute_liquidation(self, ticker: str, mark_price: float) -> None:
        """강제 청산 실행"""

    def get_total_unrealized_pnl(self, mark_prices: dict[str, float]) -> float:
        """전체 미실현 손익"""

    def get_available_margin(self, mark_prices: dict[str, float]) -> float:
        """가용 증거금 (출금/신규 주문 가능 금액)"""
```

#### 6. 청산 로직

- **증거금률 계산**: `margin_ratio = margin / position_value`
- **청산 조건**: `margin_ratio < maintenance_margin_ratio`
- **청산 가격 계산**:
  - Long: `liquidation_price = entry_price * (1 - 1 / leverage + maintenance_margin_ratio)`
  - Short: `liquidation_price = entry_price * (1 + 1 / leverage - maintenance_margin_ratio)`

#### 7. FuturesLedger

포지션 변화 및 손익 추적

```python
class FuturesLedger:
    ticker: str
    _entries: list[FuturesLedgerEntry]

    def add_trade(self, trade: FuturesTrade) -> FuturesLedgerEntry:
        """거래 기록 및 손익 계산"""

    def add_funding_fee(self, amount: float, timestamp: int) -> None:
        """자금 조달 수수료 기록"""

    def to_dataframe(self) -> pd.DataFrame:
        """DataFrame 변환"""
```

---

### Phase 3: 고급 기능

선택적이지만 실전 거래 시뮬레이션에 유용합니다.

#### 8. 자금 조달 수수료 (Funding Fee)

- 주기적 수수료 교환 (일반적으로 8시간마다)
- Funding Rate > 0: Long이 Short에 지불
- Funding Rate < 0: Short이 Long에 지불
- 계산: `funding_fee = position_value * funding_rate`

#### 9. TP/SL 통합 주문

- 진입 주문 시 TP/SL 가격 동시 설정
- 조건 충족 시 자동 청산 주문 실행
- 주문 관리: `FuturesOrderManager` 필요

#### 10. Reduce-only 주문

- 포지션 증가 방지
- 현재 포지션 수량을 초과하는 주문 거부
- 청산 전용 주문에 사용

---

## 구현 우선순위

### 1단계: 최소 기능 세트 (MVP)

```
FuturesSide → FuturesPosition → FuturesTrade → FuturesOrder
```

- 데이터 구조만 완성하면 테스트 가능
- 다른 기능의 기반 제공

### 2단계: 핵심 거래 기능

```
FuturesWallet (증거금 + 포지션 관리 + 청산)
FuturesLedger
```

- 실제 시뮬레이션 가능
- 기본적인 거래 흐름 구현

### 3단계: 실전 기능

```
Funding Fee → TP/SL → Reduce-only
```

- 현실적인 시뮬레이션
- 실전 거래소와 유사한 환경 제공

---

## 구현 시 주의사항

### 1. 불변성 유지
- SpotOrder와 동일한 불변 복제 패턴 적용
- 상태 변경 시 새 인스턴스 반환

### 2. 레버리지 검증
- 1x ~ 125x 범위 체크
- 거래소별 최대 레버리지 제한 고려

### 3. 증거금 부족 체크
- 주문 생성 전 가용 증거금 검증
- 증거금 출금 시 유지 증거금 확인

### 4. 청산 우선순위
- 거래 처리 전 항상 청산 체크
- 마크가격 기준으로 청산 판단

### 5. 포지션 방향 관리
- Long/Short 별도 관리
- 양방향 포지션 지원 여부 결정 필요 (Hedge Mode vs One-way Mode)

### 6. 정밀도 및 반올림
- 가격/수량 소수점 정밀도 관리
- 최소 거래 단위 준수

### 7. 테스트 전략
- 단위 테스트: 각 컴포넌트 독립 테스트
- 통합 테스트: Wallet + Position + Ledger 연동
- 시나리오 테스트: 실제 거래 시퀀스 시뮬레이션
- 청산 시나리오 테스트: 다양한 레버리지/가격 변동 조건

---

## 참고사항

- 기존 Spot 거래 시스템과 최대한 일관된 인터페이스 유지
- `financial-simulation` 패키지와의 통합 고려 (TradeSimulation 확장)
- 실제 거래소 API (Binance, Bybit 등)와 호환 가능한 데이터 구조 설계
