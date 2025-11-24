# Core 계층

Core 계층은 MultiCandle의 핵심 알고리즘과 데이터 처리 로직을 제공합니다.
모든 Core 모듈은 stateless 정적 메서드로 구현됩니다.

## TensorBuilder

List[Candle] → 3D numpy 텐서 변환. 타임스탬프 합집합 수집, 종목 정렬, 텐서 구축.

build(candles: List[Candle]) -> tuple[np.ndarray, list[str], np.ndarray[int]]
    Candle 리스트를 3D 텐서로 변환

## IndexMapper

symbol/timestamp 양방향 매핑 생성 및 관리.

build_symbol_mapping(symbols: list[str]) -> tuple[dict[str, int], list[str]]
    종목 → 인덱스 매핑 생성

build_timestamp_mapping(timestamps: np.ndarray[int]) -> tuple[dict[int, int], np.ndarray[int]]
    타임스탬프 → 인덱스 매핑 생성

## QueryExecutor

텐서 슬라이싱을 통한 조회 로직. numpy array → Price 객체 변환.

get_snapshot_data(tensor: np.ndarray, timestamp_idx: int, symbols: list[str], exchange: str, timestamp: int, as_price: bool) -> np.ndarray | dict[str, Price]
    시점 기반 조회

get_symbol_range_data(tensor: np.ndarray, symbol_idx: int, start_idx: int, end_idx: int, symbol: str, exchange: str, timestamps: np.ndarray, as_price: bool) -> np.ndarray | List[Price]
    종목 기반 범위 조회

get_range_data(tensor: np.ndarray, start_idx: int, end_idx: int) -> np.ndarray
    범위 기반 조회
