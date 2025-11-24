# MultiCandle

여러 종목의 캔들 데이터를 통합 관리하고 효율적으로 조회하는 컨트롤러 클래스.
시뮬레이션 및 분석용 고성능 조회 인터페이스 제공.

_tensor: np.ndarray                     # (n_symbols, n_timestamps, 5) 3D 텐서
_symbols: list[str]                     # 종목 리스트 (시작 시점 빠른 순 정렬)
_timestamps: np.ndarray[int]            # 타임스탬프 배열 (시간 순 정렬)
_symbol_to_idx: dict[str, int]          # 종목 → 인덱스 매핑
_timestamp_to_idx: dict[int, int]       # 타임스탬프 → 인덱스 매핑
_exchange: str                          # 거래소명

## 초기화

__init__(candles: List[Candle]) -> None
    여러 Candle 객체로 MultiCandle 초기화. 3D 텐서 구축 및 매핑 생성.

    Args:
        candles: Candle 객체 리스트 (동일 exchange, timeframe 가정)

    Raises:
        ValueError: candles가 비어있는 경우
        ValueError: candles의 exchange가 다른 경우

    Notes:
        - 모든 데이터를 온메모리로 로드 (GB 단위 가능)
        - 초기화 후 불변 (read-only)
        - TensorBuilder로 텐서 구축
        - IndexMapper로 매핑 생성

## 시점 기반 조회

get_snapshot(timestamp: int, as_price: bool = False) -> np.ndarray | dict[str, Price]
    특정 시점의 모든 종목 스냅샷 조회. 시뮬레이션 메인 루프에서 사용.

    Args:
        timestamp: 조회할 타임스탬프 (초 단위)
        as_price: True면 Price 객체 dict 반환, False면 numpy array 반환 (기본값: False)

    Returns:
        as_price=False: np.ndarray, shape (n_symbols, 5), dtype float64
            - 각 행: [open, high, low, close, volume]
            - NaN 포함 가능 (해당 시점에 데이터 없는 종목)
        as_price=True: dict[str, Price]
            - key: 종목명 (예: "BTC/USDT")
            - value: Price 객체
            - NaN인 종목은 dict에 포함 안 됨

    Raises:
        KeyError: timestamp가 존재하지 않는 경우

    Notes:
        - O(1) 인덱싱 + O(n_symbols) 복사
        - 가장 빈번히 호출되는 메서드
        - QueryExecutor.get_snapshot_data 사용

## 종목 기반 조회

get_symbol_range(symbol: str, start_ts: int, end_ts: int, as_price: bool = False) -> np.ndarray | List[Price]
    특정 종목의 시간 범위 데이터 조회. 분석 및 백테스팅용.

    Args:
        symbol: 종목명 (예: "BTC/USDT")
        start_ts: 시작 타임스탬프 (포함)
        end_ts: 종료 타임스탬프 (미포함)
        as_price: True면 Price 객체 리스트 반환 (기본값: False)

    Returns:
        as_price=False: np.ndarray, shape (n_times, 5)
            - 각 행: [open, high, low, close, volume]
        as_price=True: List[Price]
            - Price 객체 리스트 (시간 순)

    Raises:
        KeyError: symbol이 존재하지 않는 경우
        KeyError: start_ts 또는 end_ts가 범위 밖인 경우

    Notes:
        - O(1) 인덱싱 + O(n_times) 복사
        - NaN 포함 가능
        - QueryExecutor.get_symbol_range_data 사용

## 범위 기반 조회

get_range(start_ts: int, end_ts: int, as_price: bool = False) -> np.ndarray
    시간 범위 내 모든 종목 데이터 조회.

    Args:
        start_ts: 시작 타임스탬프 (포함)
        end_ts: 종료 타임스탬프 (미포함)
        as_price: 현재 지원 안 됨 (추후 확장)

    Returns:
        np.ndarray, shape (n_symbols, n_times, 5)
            - 3D 텐서의 시간 범위 슬라이스

    Raises:
        KeyError: start_ts 또는 end_ts가 범위 밖인 경우

    Notes:
        - O(n_symbols × n_times) 슬라이싱
        - QueryExecutor.get_range_data 사용

## 시간 반복자

iter_time(start_ts: int, end_ts: int, as_price: bool = False) -> Iterator[tuple[int, np.ndarray | dict]]
    시간 순회 반복자. 각 시점의 스냅샷을 순차 반환.

    Args:
        start_ts: 시작 타임스탬프 (포함)
        end_ts: 종료 타임스탬프 (미포함)
        as_price: True면 Price dict 반환, False면 numpy array 반환

    Yields:
        tuple[int, np.ndarray | dict[str, Price]]
            - timestamp: 현재 타임스탬프
            - data: 해당 시점의 스냅샷 (형식은 as_price에 따름)

    Raises:
        KeyError: start_ts 또는 end_ts가 범위 밖인 경우

    Notes:
        - get_snapshot을 반복 호출
        - 메모리 효율적 (한 시점씩 yield)

## 매핑 유틸리티

symbol_to_idx(symbol: str) -> int
    종목명을 텐서 인덱스로 변환.

    Args:
        symbol: 종목명 (예: "BTC/USDT")

    Returns:
        int: 텐서의 axis 0 인덱스

    Raises:
        KeyError: symbol이 존재하지 않는 경우

idx_to_symbol(idx: int) -> str
    텐서 인덱스를 종목명으로 변환.

    Args:
        idx: 텐서의 axis 0 인덱스

    Returns:
        str: 종목명

    Raises:
        IndexError: idx가 범위 밖인 경우

timestamp_to_idx(timestamp: int) -> int
    타임스탬프를 텐서 인덱스로 변환.

    Args:
        timestamp: 타임스탬프 (초 단위)

    Returns:
        int: 텐서의 axis 1 인덱스

    Raises:
        KeyError: timestamp가 존재하지 않는 경우

idx_to_timestamp(idx: int) -> int
    텐서 인덱스를 타임스탬프로 변환.

    Args:
        idx: 텐서의 axis 1 인덱스

    Returns:
        int: 타임스탬프 (초 단위)

    Raises:
        IndexError: idx가 범위 밖인 경우

---

**사용 예시:**

```python
from financial_assets.candle import Candle
from financial_assets.stock_address import StockAddress
from financial_assets.multicandle import MultiCandle

# 여러 종목 Candle 로드
addresses = [
    StockAddress("candle", "binance", "spot", "BTC", "USDT", "1m"),
    StockAddress("candle", "binance", "spot", "ETH", "USDT", "1m"),
]
candles = [Candle.load(addr, start_ts=1609459200, end_ts=1609545600) for addr in addresses]

# MultiCandle 초기화
mc = MultiCandle(candles)

# 시점 기반 조회 (numpy array - 빠름)
snapshot_array = mc.get_snapshot(1609459200)  # shape: (2, 5)
print(snapshot_array[0])  # BTC: [o, h, l, c, v]

# 시점 기반 조회 (Price 객체 - 편의성)
snapshot_dict = mc.get_snapshot(1609459200, as_price=True)
print(snapshot_dict["BTC/USDT"].c)  # BTC 종가

# 종목 기반 조회
btc_data = mc.get_symbol_range("BTC/USDT", 1609459200, 1609462800)  # shape: (60, 5)

# 시간 반복자
for timestamp, snapshot in mc.iter_time(1609459200, 1609462800):
    # 시뮬레이션 로직
    process(timestamp, snapshot)

# 매핑 유틸리티
btc_idx = mc.symbol_to_idx("BTC/USDT")  # 0
timestamp_idx = mc.timestamp_to_idx(1609459200)  # 0
```

**의존성:**
- financial_assets.candle.Candle: 단일 종목 캔들 데이터
- financial_assets.price.Price: OHLCV 데이터 구조
- numpy: 텐서 연산
- simple_logger: 로깅 데코레이터 (@init_logging, @func_logging)
- Core.TensorBuilder: 텐서 구축
- Core.IndexMapper: 매핑 생성
- Core.QueryExecutor: 조회 실행

**성능 특성:**
- 초기화: O(n_symbols × n_timestamps), GB 단위 메모리
- get_snapshot: O(n_symbols), 메인 루프에서 빈번히 호출
- get_symbol_range: O(n_times), 분석용
- iter_time: O(n_symbols) per iteration
