# MarketData

MultiCandle 기반 시뮬레이션 시장 데이터 관리. 커서 관리 레이어 추가하여 시점 추적 및 가격 조회 API 제공.

## 속성

_multicandle: MultiCandle       # 실제 캔들 데이터 보관소
_timestamps: np.ndarray          # 전체 타임스탬프 배열
_n_timestamps: int               # 타임스탬프 총 개수
_start_offset: int               # 시작 오프셋 (인덱스)
_random_offset: bool             # 랜덤 오프셋 활성화 여부
_start_idx: int                  # 실제 시작 인덱스 (offset + random 적용)
_cursor_idx: int                 # 현재 커서 인덱스

## 메서드

### 초기화

__init__(multicandle: MultiCandle, start_offset: int = 0, random_offset: bool = False) -> None
    MarketData 초기화 및 시작 커서 계산

### 커서 제어

reset(override: bool = False) -> None
    커서를 시작 위치로 리셋 (override=True면 새로운 랜덤 시작점 생성)

step() -> bool
    다음 타임스탬프로 이동 (성공 시 True, 끝 도달 시 False)

### 가격 조회

get_current(symbol: str | Symbol) -> Price
    raise KeyError
    특정 심볼의 현재 커서 위치 가격 조회

get_current_all() -> dict[str, Price]
    현재 커서 위치의 모든 유효한 심볼 가격 조회

get_current_timestamp() -> int
    현재 커서 위치의 타임스탬프 조회

### 메타 정보

get_symbols() -> list[str]
    관리 중인 모든 심볼 리스트

get_cursor_idx() -> int
    현재 커서 인덱스 조회

is_finished() -> bool
    시뮬레이션 종료 여부 (커서가 마지막 위치 도달)

get_progress() -> float
    시뮬레이션 진행률 (0.0 ~ 1.0)

### 캔들 데이터

get_candles(symbol: str | Symbol, start_ts: int = None, end_ts: int = None, limit: int = None) -> pd.DataFrame
    raise KeyError
    과거 캔들 데이터 조회 (MultiCandle의 고정 timeframe 사용)

    Args:
        symbol: 심볼 (예: "BTC/USDT") 또는 Symbol 객체
        start_ts: 시작 타임스탬프 (None이면 처음부터)
        end_ts: 종료 타임스탬프 (None이면 현재 커서까지, 커서 포함)
        limit: 최대 개수 (None이면 전체, 지정 시 최근 데이터부터 limit개)

    Returns:
        pd.DataFrame: 캔들 데이터 (columns: timestamp, open, high, low, close, volume)

---

## Symbol 지원

모든 symbol 파라미터는 `str | Symbol` 타입 지원:
- str: "BTC/USDT" (slash 형식)
- Symbol: Symbol("BTC/USDT") 또는 Symbol("BTC-USDT")

내부 변환:
- `str(symbol)` → "BTC/USDT" (MultiCandle 키 접근용)

---

## 시간 동기화

- 단일 커서로 모든 심볼 동기화
- MultiCandle 내부에서 심볼별 데이터 길이 관리
- step() 호출 시 모든 심볼이 동일 시점으로 이동

---

## 시작점 계산

1. start_offset 적용 (지표 계산 마진 등)
2. random_offset=True이면:
   - 남은 길이의 절반 범위 내에서 랜덤 오프셋 추가
   - 매 reset(override=True) 호출 시 새로운 랜덤 시작점 생성
3. 범위 체크 후 _start_idx 결정
4. _cursor_idx를 _start_idx로 초기화

---

## 의존성

- MultiCandle: 실제 캔들 데이터 저장소 (financial-assets)
- Price: OHLCV 데이터 구조체 (financial-assets)
