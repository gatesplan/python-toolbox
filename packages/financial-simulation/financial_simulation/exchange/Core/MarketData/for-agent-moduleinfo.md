# MarketData
시장 데이터 및 커서 관리. 심볼별 캔들 데이터를 보관하고, 현재 시점을 추적하며, 가격 조회 API를 제공합니다.

## 책임 범위
- 심볼별 캔들 데이터 저장 및 관리
- 전역 커서로 현재 시점 추적 (모든 심볼 동기화)
- step() 호출 시 다음 틱으로 이동
- 심볼별 현재 가격 조회
- 시뮬레이션 진행 상태 제공

## 주요 속성

_data: dict[str, list[Price]]    # {symbol: [Price, ...]}
_cursor: int                     # 현재 인덱스 (모든 심볼 공통)
_max_length: int                 # 가장 긴 데이터 길이
_start_cursor: int               # 합리적 시작 지점
_base_start_cursor: int          # offset 적용 전 기본 시작 지점
_availability_threshold: float   # 데이터 유효성 임계값
_offset: int                     # 고정 오프셋
_random_additional_offset: bool  # 랜덤 오프셋 활성화 여부

## 주요 메서드

### 초기화 및 리셋

__init__(
    data: dict[str, list[Price]],
    availability_threshold: float = 0.8,
    offset: int = 0,
    random_additional_offset: bool = False
) -> None
    MarketData 초기화 및 합리적 시작 커서 설정

    Args:
        data: 심볼별 가격 데이터 딕셔너리
              예: {"BTC/USDT": [...], "ETH/USDT": [...]}
        availability_threshold: 데이터 유효성 임계값 (기본: 0.8)
                                이 비율 이상의 심볼이 데이터를 가진 시점을 시작점으로
        offset: 시작점에서 추가로 이동할 오프셋 (지표 계산 마진 등)
        random_additional_offset: True면 시작점을 랜덤화 (남은 데이터 길이의 절반까지)

    Raises:
        ValueError: 데이터가 비어있거나 합리적 시작점을 찾을 수 없는 경우

    Returns:
        None

    Note:
        - 합리적 시작 커서 = find_valid_start_cursor() + offset + (random_offset if enabled)
        - random_offset 범위: 0 ~ (max_length - start_cursor) // 2

reset(override: bool = False) -> None
    커서를 시작 위치로 리셋

    Args:
        override: True면 새로운 랜덤 시작 커서를 생성, False면 기존 _start_cursor 사용

    Returns:
        None

    Note:
        - override=False (기본값): _start_cursor로 복원
        - override=True: random_additional_offset이 활성화된 경우에만 새로운 랜덤 시작점 생성
        - 새로운 random_offset = 0 ~ (max_length - base_start_cursor) // 2
        - _start_cursor와 _cursor를 새로운 값으로 업데이트

### 커서 이동

step() -> bool
    다음 틱으로 이동 (모든 심볼 동기화)

    Returns:
        bool: 이동 성공 여부. False면 데이터 끝에 도달

### 데이터 조회

get_current(symbol: str) -> Price | None
    특정 심볼의 현재 커서 위치 가격 데이터 조회

    Args:
        symbol: 거래쌍 심볼 (예: "BTC/USDT")

    Returns:
        Price | None: 현재 가격 데이터. 심볼이 없거나 범위 밖이면 None

    Note:
        심볼별 데이터 길이가 다를 수 있으므로 None 반환 가능

get_current_all() -> dict[str, Price]
    현재 커서 위치에서 유효한 모든 심볼의 가격 데이터 조회

    Returns:
        dict[str, Price]: {symbol: current_price}
                          범위 밖인 심볼은 제외됨

get_current_timestamp(symbol: str) -> int | None
    특정 심볼의 현재 타임스탬프 조회

    Args:
        symbol: 거래쌍 심볼

    Returns:
        int | None: 현재 타임스탬프. 심볼이 없거나 범위 밖이면 None

get_symbols() -> list[str]
    관리 중인 모든 심볼 리스트

    Returns:
        list[str]: 심볼 리스트

### 상태 조회

get_cursor() -> int
    현재 커서 위치 조회

    Returns:
        int: 현재 인덱스

get_max_length() -> int
    가장 긴 데이터 길이 조회

    Returns:
        int: 최대 데이터 길이

is_finished() -> bool
    시뮬레이션 종료 여부 (커서가 최대 길이 도달)

    Returns:
        bool: 종료 여부

get_progress() -> float
    시뮬레이션 진행률 (0.0 ~ 1.0)

    Returns:
        float: 진행률 (cursor / max_length)

get_availability(cursor_position: int | None = None) -> float
    특정 커서 위치의 데이터 유효성 비율

    Args:
        cursor_position: 확인할 커서 위치 (None이면 현재 커서)

    Returns:
        float: 유효성 비율 (0.0 ~ 1.0)
               유효한 심볼 수 / 전체 심볼 수

---

## 사용 예시

```python
# 심볼별 가격 데이터 준비
market_data = {
    "BTC/USDT": [
        Price(t=1000, o=50000, h=51000, l=49000, c=50500, v=100),
        Price(t=2000, o=50500, h=52000, l=50000, c=51000, v=150),
    ],
    "ETH/USDT": [
        Price(t=1000, o=3000, h=3100, l=2900, c=3050, v=200),
        Price(t=2000, o=3050, h=3200, l=3000, c=3150, v=250),
    ]
}

# MarketData 생성
market = MarketData(market_data)

# 시뮬레이션 루프
while not market.is_finished():
    # 현재 가격 조회
    btc_price = market.get_current("BTC/USDT")
    eth_price = market.get_current("ETH/USDT")

    print(f"BTC: {btc_price.c}, ETH: {eth_price.c}")

    # 다음 틱으로 이동 (모든 심볼 동기화)
    market.step()

# 기본 리셋 (동일한 시작점으로 복원)
market.reset()

# 랜덤 시작점으로 리셋 (random_additional_offset=True인 경우)
market_random = MarketData(market_data, random_additional_offset=True)
market_random.reset(override=True)  # 매번 다른 시작점
```

## 설계 노트

**시간 동기화:**
- 심볼별 데이터 길이가 다를 수 있음 (실제 데이터 반영)
- 단일 커서로 모든 심볼을 동기화하여 이동
- step() 호출 시 유효한 심볼들이 동시에 다음 시점으로

**합리적 시작점 탐색:**
1. 각 인덱스에서 데이터 유효성 계산 (유효 심볼 수 / 전체 심볼 수)
2. availability_threshold(기본 0.8) 이상인 첫 번째 인덱스 찾기
3. offset 추가 (지표 계산 마진 등)
4. random_additional_offset이면 추가 랜덤 오프셋 적용

**데이터 유효성:**
- get_current(symbol) 호출 시 범위 밖이면 None 반환
- get_current_all()은 유효한 심볼만 포함
- 유효성 비율이 낮아지면 시뮬레이션 종료 고려

**메모리:**
- 전체 데이터를 메모리에 보유 (백테스팅 용도)
- 실시간 스트리밍은 현재 범위 밖

**확장성:**
- 향후 실시간 스트리밍 지원 시 상속 또는 Strategy 패턴 고려
