# MathUtils
순수 수학 유틸리티. 외부 의존 없는 기본 연산을 제공한다.

`round_to_min_unit(value: float, min_unit: float) -> float`
값을 최소 단위의 배수로 내림한다.


# CandleAnalyzer
캔들 영역 분석. 목표 가격이 캔들의 어느 영역에 속하는지 분류한다.

`classify_zone(price, target_price: float) -> str`
캔들에서 목표 가격이 위치한 영역을 분류한다. "body", "head", "tail", "none" 중 하나를 반환한다.


# PriceSampler
가격 샘플링. 정규분포 기반 가격 샘플링 및 통계 파라미터 계산을 제공한다.

`calculate_normal_params(range_min: float, range_max: float, std_factor: int = 4) -> tuple[float, float]`
범위로부터 정규분포의 mean과 std를 계산한다.

`sample_from_normal(min_price: float, max_price: float, mean: float, std: float, min_z: float = -2.0, max_z: float = 2.0) -> float`
정규분포 기반 가격 샘플링을 수행한다. z-score 클리핑 및 범위 클리핑을 적용한다.


# SlippageCalculator
슬리피지 범위 계산. 주문 방향에 따라 불리한 체결 가격 범위를 계산한다.

`calculate_range(price, side) -> tuple[float, float]`
- raise ValueError: 알 수 없는 side
주문 방향(BUY/SELL)에 따른 슬리피지 범위를 계산한다. BUY는 head 범위, SELL은 tail 범위를 반환한다.


# AmountSplitter
수량 분할. Dirichlet 분포를 사용하여 수량을 여러 조각으로 랜덤 분할한다.

`split_with_dirichlet(total_amount: float, min_amount: float, split_count: int) -> List[float]`
전체 수량을 split_count개로 분할한다. 각 조각은 min_amount의 배수로 조정되며, 잔여량은 마지막 조각에 추가된다.
