# MarketData
시장 데이터 및 커서 관리. 심볼별 캔들 데이터 보관, 현재 시점 추적, 가격 조회 API 제공.

_data: dict[str, list[Price]]    # {symbol: [Price, ...]}
_cursor: int                     # 현재 인덱스 (모든 심볼 공통)
_max_length: int                 # 가장 긴 데이터 길이
_start_cursor: int               # 합리적 시작 지점
_base_start_cursor: int          # offset 적용 전 기본 시작 지점
_availability_threshold: float   # 데이터 유효성 임계값
_offset: int                     # 고정 오프셋
_random_additional_offset: bool  # 랜덤 오프셋 활성화 여부

__init__(data: dict[str, list[Price]], availability_threshold: float = 0.8, offset: int = 0, random_additional_offset: bool = False) -> None
    raise ValueError
    MarketData 초기화 및 합리적 시작 커서 설정

reset(override: bool = False) -> None
    커서를 시작 위치로 리셋 (override=True면 새로운 랜덤 시작점 생성)

step() -> bool
    다음 틱으로 이동 (모든 심볼 동기화). False면 데이터 끝 도달

get_current(symbol: str) -> Price | None
    특정 심볼의 현재 커서 위치 가격 데이터 조회

get_current_all() -> dict[str, Price]
    현재 커서 위치에서 유효한 모든 심볼의 가격 데이터 조회

get_current_timestamp(symbol: str) -> int | None
    특정 심볼의 현재 타임스탬프 조회

get_symbols() -> list[str]
    관리 중인 모든 심볼 리스트

get_cursor() -> int
    현재 커서 위치 조회

get_max_length() -> int
    가장 긴 데이터 길이 조회

is_finished() -> bool
    시뮬레이션 종료 여부 (커서가 최대 길이 도달)

get_progress() -> float
    시뮬레이션 진행률 (0.0 ~ 1.0)

get_availability(cursor_position: int | None = None) -> float
    특정 커서 위치의 데이터 유효성 비율

---

**시간 동기화:**
- 심볼별 데이터 길이가 다를 수 있음
- 단일 커서로 모든 심볼을 동기화하여 이동
- step() 호출 시 유효한 심볼들이 동시에 다음 시점으로

**합리적 시작점 탐색:**
1. 각 인덱스에서 데이터 유효성 계산 (유효 심볼 수 / 전체 심볼 수)
2. availability_threshold(기본 0.8) 이상인 첫 번째 인덱스 찾기
3. offset 추가 (지표 계산 마진 등)
4. random_additional_offset이면 추가 랜덤 오프셋 적용
