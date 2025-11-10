# FillProbability
체결 확률 상수 정의.

`BODY_FULL: float = 1.0` body 범위에서 전량 체결 확률
`WICK_FAIL: float = 0.3` wick 범위에서 체결 실패 확률
`WICK_FULL: float = 0.3` wick 범위에서 전량 체결 확률
`WICK_PARTIAL: float = 0.4` wick 범위에서 부분 체결 확률


# SplitConfig
수량 분할 설정 상수 정의.

`MIN_SPLIT_COUNT: int = 1` 최소 분할 개수
`MAX_SPLIT_COUNT: int = 3` 최대 분할 개수
`MIN_TRADE_AMOUNT_RATIO: float = 0.01` 최소 거래 금액 비율 (기본값)
`STD_CALCULATION_FACTOR: int = 4` 표준편차 계산 계수 (std = range / 4)
