# 현물 거래 장부 모듈 추가

## 왜 필요한가

아키텍처 문서(Architecture - Trading Sim.md)에서 Wallet이 거래 처리 시 "자산 조정 및 장부 작성"을 수행해야 한다고 명시되어 있습니다. 현재는 현물 거래의 거래 이력을 추적하고 누적 지표를 계산하는 장부 모듈이 없습니다.

장부가 필요한 이유:
- 단일 거래쌍의 모든 거래 기록 보관
- 누적 자산 및 가치 포지션 추적
- 평균 진입가 계산
- 실현 손익 계산
- 거래 내역 분석 및 리포팅

이 모듈은 Wallet의 장부 기록 책임을 지원하기 위해 현물 거래 전용 `SpotLedger`와 `SpotLedgerEntry`를 구현합니다.

Ledger는 **데이터 테이블 역할**에 집중하며, 통계 계산은 상위 레이어에서 DataFrame을 받아 처리합니다.

## 무엇이 바뀌나

`financial_assets` 하위에 새로운 `ledger` 모듈 추가:

**새 파일:**
- `financial_assets/ledger/spot_ledger_entry.py` - 개별 거래 이벤트 레코드
- `financial_assets/ledger/spot_ledger.py` - 장부 컨테이너
- `financial_assets/ledger/__init__.py` - 모듈 export
- `tests/test_spot_ledger.py` - 테스트

**SpotLedgerEntry (불변 dataclass):**
```python
@dataclass(frozen=True)
class SpotLedgerEntry:
    timestamp: int                # 거래 시각 (Unix timestamp)
    trade: SpotTrade              # 원본 거래
    asset_change: float           # 자산 변화량 (+ 증가, - 감소)
    value_change: float           # 가치 변화량 (+ 증가, - 감소)
    cumulative_asset: float       # 누적 자산 보유량
    cumulative_value: float       # 누적 가치 (투자금)
    average_price: float          # 평균 진입가
    realized_pnl: Optional[float] # 실현 손익 (SELL 시에만)
```

**SpotLedger (가변 container):**
```python
class SpotLedger:
    def __init__(self, ticker: str) -> None
        """거래쌍(예: "BTC-USDT")에 대한 장부 초기화"""

    def add_trade(self, trade: SpotTrade) -> SpotLedgerEntry
        """거래를 장부에 기록하고 SpotLedgerEntry 반환
        - BUY: 자산 증가, 평균가 재계산
        - SELL: 자산 감소, 실현손익 계산
        """

    def to_dataframe(self) -> pd.DataFrame
        """모든 거래 내역을 pandas DataFrame으로 반환
        컬럼: timestamp, side, asset_change, value_change,
              cumulative_asset, cumulative_value, average_price, realized_pnl
        """
```

**주요 로직:**
- BUY 거래 시: 가중 평균으로 평균 진입가 재계산
- SELL 거래 시: `(매도가 - 평균가) * 수량`으로 실현 손익 계산
- 포지션 완전 청산 시: 평균가를 None으로 리셋
- DataFrame 변환을 통해 상위 레이어에서 자유롭게 분석/시각화

## 영향 범위

- **영향받는 spec**: 없음 (신규 spec: `spot-ledger-data-structure`)
- **신규 코드**:
  - `financial_assets/ledger/spot_ledger_entry.py`
  - `financial_assets/ledger/spot_ledger.py`
  - `financial_assets/ledger/__init__.py`
  - `tests/test_spot_ledger.py`
- **의존성**: 기존 `SpotTrade`, `SpotSide`, `Token`, `Pair` 모듈 필요
- **마이그레이션**: 없음 (추가 기능만)
