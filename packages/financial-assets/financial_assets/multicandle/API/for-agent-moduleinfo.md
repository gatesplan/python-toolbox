# API 계층 (Controller)

API 계층은 MultiCandle 모듈의 공개 인터페이스를 제공합니다.

## MultiCandle

여러 종목의 캔들 데이터 조회 인터페이스. 시뮬레이션 및 분석용 고성능 조회 제공.

_tensor: np.ndarray                     # (n_symbols, n_timestamps, 5) 3D 텐서
_symbols: list[str]                     # 종목 리스트 (정렬됨)
_timestamps: np.ndarray[int]            # 타임스탬프 배열 (정렬됨)
_symbol_to_idx: dict[str, int]          # 종목 → 인덱스 매핑
_timestamp_to_idx: dict[int, int]       # 타임스탬프 → 인덱스 매핑
_exchange: str                          # 거래소명

__init__(candles: List[Candle]) -> None
    여러 Candle 객체로 MultiCandle 초기화

get_snapshot(timestamp: int, as_price: bool = False) -> np.ndarray | dict[str, Price]
    특정 시점의 모든 종목 스냅샷 조회 (시점 기반 조회)

get_symbol_range(symbol: str, start_ts: int, end_ts: int, as_price: bool = False) -> np.ndarray | List[Price]
    특정 종목의 시간 범위 데이터 조회 (종목 기반 조회)

get_range(start_ts: int, end_ts: int, as_price: bool = False) -> np.ndarray
    시간 범위 내 모든 종목 데이터 조회 (범위 기반 조회)

iter_time(start_ts: int, end_ts: int, as_price: bool = False) -> Iterator[tuple[int, np.ndarray | dict]]
    시간 순회 반복자 (시간 반복자)

symbol_to_idx(symbol: str) -> int
    종목명 → 인덱스 변환

idx_to_symbol(idx: int) -> str
    인덱스 → 종목명 변환

timestamp_to_idx(timestamp: int) -> int
    타임스탬프 → 인덱스 변환

idx_to_timestamp(idx: int) -> int
    인덱스 → 타임스탬프 변환
