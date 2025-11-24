# IndexMapper

symbol/timestamp와 텐서 인덱스 간 양방향 매핑을 생성하는 정적 유틸리티 클래스.
O(1) 조회 성능을 위한 dict 기반 매핑 제공.

## 종목 매핑

build_symbol_mapping(symbols: list[str]) -> tuple[dict[str, int], list[str]]
    종목명과 인덱스 간 양방향 매핑 생성.

    Args:
        symbols: 종목 리스트 (정렬된 상태, 예: ["BTC/USDT", "ETH/USDT"])

    Returns:
        tuple[dict[str, int], list[str]]:
            - symbol_to_idx: 종목명 → 인덱스 매핑 (예: {"BTC/USDT": 0, "ETH/USDT": 1})
            - idx_to_symbol: 인덱스 → 종목명 리스트 (입력 symbols와 동일)

    Raises:
        ValueError: symbols가 비어있는 경우
        ValueError: symbols에 중복이 있는 경우

    Notes:
        - O(n) 생성, O(1) 조회
        - symbol_to_idx는 dict로 빠른 조회
        - idx_to_symbol은 list로 순차 접근

## 타임스탬프 매핑

build_timestamp_mapping(timestamps: np.ndarray[int]) -> tuple[dict[int, int], np.ndarray[int]]
    타임스탬프와 인덱스 간 양방향 매핑 생성.

    Args:
        timestamps: 타임스탬프 배열 (정렬된 상태, 초 단위)

    Returns:
        tuple[dict[int, int], np.ndarray[int]]:
            - timestamp_to_idx: 타임스탬프 → 인덱스 매핑 (예: {1609459200: 0, 1609459260: 1})
            - idx_to_timestamp: 인덱스 → 타임스탬프 배열 (입력 timestamps와 동일)

    Raises:
        ValueError: timestamps가 비어있는 경우
        ValueError: timestamps에 중복이 있는 경우

    Notes:
        - O(n) 생성, O(1) 조회
        - timestamp_to_idx는 dict로 빠른 조회
        - idx_to_timestamp는 numpy array로 벡터 연산 가능

---

**사용 예시:**

```python
from financial_assets.multicandle.Core.IndexMapper import IndexMapper
import numpy as np

# 종목 매핑 생성
symbols = ["BTC/USDT", "ETH/USDT", "XRP/USDT"]
symbol_to_idx, idx_to_symbol = IndexMapper.build_symbol_mapping(symbols)

# 종목 → 인덱스
btc_idx = symbol_to_idx["BTC/USDT"]  # 0

# 인덱스 → 종목
symbol = idx_to_symbol[0]  # "BTC/USDT"

# 타임스탬프 매핑 생성
timestamps = np.array([1609459200, 1609459260, 1609459320])
timestamp_to_idx, idx_to_timestamp = IndexMapper.build_timestamp_mapping(timestamps)

# 타임스탬프 → 인덱스
ts_idx = timestamp_to_idx[1609459200]  # 0

# 인덱스 → 타임스탬프
ts = idx_to_timestamp[0]  # 1609459200
```

**의존성:**
- numpy: 배열 처리
- simple_logger: 로깅 데코레이터 (@func_logging - 정적 메서드만 사용)

**구현 세부사항:**

1. **종목 매핑:**
   - symbol_to_idx = {symbol: idx for idx, symbol in enumerate(symbols)}
   - idx_to_symbol = symbols (동일 리스트 반환)

2. **타임스탬프 매핑:**
   - timestamp_to_idx = {int(ts): idx for idx, ts in enumerate(timestamps)}
   - idx_to_timestamp = timestamps (동일 배열 반환)

3. **검증:**
   - 비어있는 입력 확인
   - 중복 확인 (len(unique) != len(input))

4. **성능 특성:**
   - 생성: O(n)
   - 조회: O(1) - dict 기반
   - 메모리: O(n) - 입력 크기에 비례
