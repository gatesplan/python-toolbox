# TensorBuilder

List[Candle] 객체들을 3D numpy 텐서로 변환하는 정적 유틸리티 클래스.
타임스탬프 합집합 수집, 종목 정렬, 텐서 할당 및 데이터 채우기 담당.

## 텐서 구축

build(candles: List[Candle]) -> tuple[np.ndarray, list[str], np.ndarray[int]]
    Candle 리스트를 3D 텐서로 변환. 타임스탬프 합집합 수집 및 종목 정렬 수행.

    Args:
        candles: Candle 객체 리스트
            - 동일 exchange, timeframe 가정
            - 각 Candle.candle_df는 이미 시간순 정렬됨

    Returns:
        tuple[np.ndarray, list[str], np.ndarray[int]]:
            - tensor: (n_symbols, n_timestamps, 5) shape의 3D array, dtype float64
                - axis 0: 종목 (시작 시점 빠른 순 정렬)
                - axis 1: 타임스탬프 (시간 순 정렬)
                - axis 2: [open, high, low, close, volume]
                - 누락 데이터는 NaN
            - symbols: 종목 리스트 (정렬됨, 예: ["BTC/USDT", "ETH/USDT"])
            - timestamps: 타임스탬프 배열 (정렬됨, 초 단위)

    Raises:
        ValueError: candles가 비어있는 경우
        ValueError: candles의 exchange가 서로 다른 경우

    Notes:
        - 알고리즘:
            1. 모든 Candle에서 timestamp 합집합 수집 (이미 정렬된 상태)
            2. 각 Candle의 (symbol, 첫_timestamp) 추출
            3. 첫_timestamp 기준으로 종목 정렬 (빠른 순)
            4. (n_symbols, n_timestamps, 5) 텐서 할당, NaN 초기화
            5. 각 Candle.candle_df를 순회하며 텐서 채우기
                - timestamp 매칭하여 올바른 인덱스에 배치
                - 컬럼 순서: open, high, low, close, volume
        - 시간 복잡도: O(n_symbols × n_timestamps)
        - 공간 복잡도: O(n_symbols × n_timestamps) - GB 단위 가능

---

**사용 예시:**

```python
from financial_assets.candle import Candle
from financial_assets.multicandle.Core.TensorBuilder import TensorBuilder

# Candle 로드
candles = [Candle.load(addr1), Candle.load(addr2)]

# 텐서 구축
tensor, symbols, timestamps = TensorBuilder.build(candles)

# 결과 확인
print(tensor.shape)  # (2, 1440, 5) - 2종목, 1440분봉, OHLCV
print(symbols)       # ["BTC/USDT", "ETH/USDT"]
print(timestamps[:5])  # [1609459200, 1609459260, ...]

# 특정 데이터 접근
btc_first_candle = tensor[0, 0, :]  # BTC의 첫 캔들: [o, h, l, c, v]
```

**의존성:**
- financial_assets.candle.Candle: 단일 종목 캔들 데이터
- numpy: 텐서 연산
- pandas: DataFrame 처리
- simple_logger: 로깅 데코레이터 (@func_logging - 정적 메서드만 사용)

**구현 세부사항:**

1. **타임스탬프 합집합 수집:**
   - 각 Candle.candle_df['timestamp']를 수집
   - np.unique로 중복 제거 및 정렬
   - 이미 정렬된 데이터이므로 추가 정렬 불필요

2. **종목 정렬:**
   - 각 Candle에서 symbol = f"{address.base}/{address.quote}"
   - 첫_timestamp = candle_df['timestamp'].iloc[0]
   - (symbol, 첫_timestamp) 리스트 생성 후 첫_timestamp 기준 정렬

3. **텐서 채우기:**
   - 각 (symbol_idx, timestamp_idx) 위치에 OHLCV 배치
   - candle_df에서 timestamp 매칭하여 올바른 인덱스 찾기
   - 누락된 경우 NaN 유지

4. **NaN 처리:**
   - 초기화 시 np.full(..., np.nan)로 전체 NaN
   - 데이터 있는 위치만 덮어쓰기
   - 누락 데이터는 자연스럽게 NaN 유지
