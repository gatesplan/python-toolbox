# QueryExecutor

텐서 슬라이싱을 통한 조회 로직을 수행하는 정적 유틸리티 클래스.
numpy array → Price 객체 변환 및 NaN 필터링 담당.

## 시점 기반 조회

get_snapshot_data(
    tensor: np.ndarray,
    timestamp_idx: int,
    symbols: list[str],
    exchange: str,
    timestamp: int,
    as_price: bool
) -> np.ndarray | dict[str, Price]
    특정 시점의 모든 종목 스냅샷 조회.

    Args:
        tensor: (n_symbols, n_timestamps, 5) 3D 텐서
        timestamp_idx: 조회할 타임스탬프의 인덱스
        symbols: 종목 리스트 (순서 중요)
        exchange: 거래소명 (Price 객체 생성용)
        timestamp: 조회할 타임스탬프 (초 단위, Price 객체 생성용)
        as_price: True면 Price 객체 dict 반환

    Returns:
        as_price=False: np.ndarray, shape (n_symbols, 5)
            - 각 행: [open, high, low, close, volume]
            - NaN 포함 가능
        as_price=True: dict[str, Price]
            - key: 종목명
            - value: Price 객체
            - NaN인 종목은 dict에 포함 안 됨

    Notes:
        - tensor[:, timestamp_idx, :] 슬라이싱 (연속 메모리 블록)
        - O(n_symbols) 복사
        - as_price=True 시 각 종목별 Price 객체 생성
        - NaN 필터링: np.isnan(row[0]) 확인 (open 값 체크)

## 종목 기반 범위 조회

get_symbol_range_data(
    tensor: np.ndarray,
    symbol_idx: int,
    start_idx: int,
    end_idx: int,
    symbol: str,
    exchange: str,
    timestamps: np.ndarray,
    as_price: bool
) -> np.ndarray | List[Price]
    특정 종목의 시간 범위 데이터 조회.

    Args:
        tensor: (n_symbols, n_timestamps, 5) 3D 텐서
        symbol_idx: 조회할 종목의 인덱스
        start_idx: 시작 타임스탬프 인덱스 (포함)
        end_idx: 종료 타임스탬프 인덱스 (미포함)
        symbol: 종목명 (Price 객체 생성용)
        exchange: 거래소명 (Price 객체 생성용)
        timestamps: 타임스탬프 배열 (Price 객체 생성용)
        as_price: True면 Price 객체 리스트 반환

    Returns:
        as_price=False: np.ndarray, shape (n_times, 5)
            - 각 행: [open, high, low, close, volume]
            - NaN 포함 가능
        as_price=True: List[Price]
            - Price 객체 리스트 (시간 순)
            - NaN인 시점은 리스트에 포함 안 됨

    Notes:
        - tensor[symbol_idx, start_idx:end_idx, :] 슬라이싱
        - O(n_times) 복사
        - as_price=True 시 각 시점별 Price 객체 생성
        - NaN 필터링: np.isnan(row[0]) 확인

## 범위 기반 조회

get_range_data(
    tensor: np.ndarray,
    start_idx: int,
    end_idx: int
) -> np.ndarray
    시간 범위 내 모든 종목 데이터 조회.

    Args:
        tensor: (n_symbols, n_timestamps, 5) 3D 텐서
        start_idx: 시작 타임스탬프 인덱스 (포함)
        end_idx: 종료 타임스탬프 인덱스 (미포함)

    Returns:
        np.ndarray, shape (n_symbols, n_times, 5)
            - 3D 텐서의 시간 범위 슬라이스

    Notes:
        - tensor[:, start_idx:end_idx, :] 슬라이싱
        - O(n_symbols × n_times) 복사
        - NaN 포함

---

**사용 예시:**

```python
from financial_assets.multicandle.Core.QueryExecutor import QueryExecutor
from financial_assets.price import Price
import numpy as np

# 텐서 및 메타데이터 준비
tensor = np.random.rand(2, 100, 5)  # (2 종목, 100 시점, OHLCV)
symbols = ["BTC/USDT", "ETH/USDT"]
timestamps = np.arange(1609459200, 1609459200 + 6000, 60)
exchange = "binance"

# 시점 기반 조회 (numpy array)
snapshot_array = QueryExecutor.get_snapshot_data(
    tensor, timestamp_idx=0, symbols=symbols,
    exchange=exchange, timestamp=timestamps[0], as_price=False
)
print(snapshot_array.shape)  # (2, 5)

# 시점 기반 조회 (Price 객체)
snapshot_dict = QueryExecutor.get_snapshot_data(
    tensor, timestamp_idx=0, symbols=symbols,
    exchange=exchange, timestamp=timestamps[0], as_price=True
)
print(snapshot_dict["BTC/USDT"].c)  # BTC 종가

# 종목 기반 범위 조회
btc_range = QueryExecutor.get_symbol_range_data(
    tensor, symbol_idx=0, start_idx=0, end_idx=10,
    symbol="BTC/USDT", exchange=exchange, timestamps=timestamps, as_price=False
)
print(btc_range.shape)  # (10, 5)

# 범위 기반 조회
range_data = QueryExecutor.get_range_data(tensor, start_idx=0, end_idx=10)
print(range_data.shape)  # (2, 10, 5)
```

**의존성:**
- financial_assets.price.Price: OHLCV 데이터 구조
- numpy: 텐서 슬라이싱 및 연산
- simple_logger: 로깅 데코레이터 (@func_logging - 정적 메서드만 사용)

**구현 세부사항:**

1. **텐서 슬라이싱:**
   - numpy의 고급 인덱싱 활용
   - 연속 메모리 블록 접근으로 캐시 효율성 극대화
   - 슬라이싱은 뷰(view)가 아닌 복사본 반환

2. **Price 객체 변환:**
   ```python
   Price(
       exchange=exchange,
       market=symbol,
       t=timestamp,
       o=row[0], h=row[1], l=row[2], c=row[3], v=row[4]
   )
   ```

3. **NaN 필터링:**
   - open 값으로 확인: np.isnan(row[0])
   - open이 NaN이면 전체 행이 NaN으로 간주
   - as_price=True 시에만 필터링 적용

4. **성능 최적화:**
   - 시점 기반: tensor[:, idx, :] → 연속 메모리 (빠름)
   - 종목 기반: tensor[idx, :, :] → stride 접근 (상대적으로 느림)
   - 범위 기반: tensor[:, start:end, :] → 대량 복사

5. **에러 처리:**
   - 인덱스 범위 검증 없음 (호출자 책임)
   - numpy가 IndexError 자동 발생
