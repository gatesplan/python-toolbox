from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Price:
    """OHLCV 가격 정보를 표현하는 캔들 데이터.
    시장 가격의 시계열 스냅샷을 제공합니다."""
    exchange: str
    market: str
    t: int
    h: float
    l: float
    o: float
    c: float
    v: float

    def __str__(self) -> str:
        return f"[{self.exchange}:{self.market}] {self.t} {self.h} {self.l} {self.o} {self.c} {self.v}"

    ########## ########## 확정적 값 생성 메서드 ########## ##########
    def bodytop(self) -> float:
        """시가와 종가 중 높은 값을 반환합니다."""
        return max(self.o, self.c)

    def bodybottom(self) -> float:
        """시가와 종가 중 낮은 값을 반환합니다."""
        return min(self.o, self.c)

    ########## ########## 범위 반환 메서드 ########## ##########
    def body(self) -> tuple[float, float]:
        """캔들 몸통의 하단과 상단을 튜플로 반환합니다."""
        return (self.bodybottom(), self.bodytop())

    def head(self) -> tuple[float, float]:
        """캔들 위 꼬리의 하단과 상단을 튜플로 반환합니다."""
        return (self.bodytop(), self.h)

    def tail(self) -> tuple[float, float]:
        """캔들 아래 꼬리의 하단과 상단을 튜플로 반환합니다."""
        return (self.l, self.bodybottom())

    def headbody(self) -> tuple[float, float]:
        """캔들 몸통 하단부터 위 꼬리 상단까지의 범위를 튜플로 반환합니다."""
        return (self.bodybottom(), self.h)

    def bodytail(self) -> tuple[float, float]:
        """캔들 아래 꼬리 하단부터 몸통 상단까지의 범위를 튜플로 반환합니다."""
        return (self.l, self.bodytop())

    ########## ########## 샘플링 메서드 ########## ##########
    def head_sample(self) -> float:
        """위 꼬리 범위에서 균등 분포 랜덤 샘플링을 수행합니다."""
        return random.uniform(*self.head())

    def tail_sample(self) -> float:
        """아래 꼬리 범위에서 균등 분포 랜덤 샘플링을 수행합니다."""
        return random.uniform(*self.tail())

    def body_sample(self) -> float:
        """몸통 범위에서 균등 분포 랜덤 샘플링을 수행합니다."""
        return random.uniform(*self.body())

    def headbody_sample(self) -> float:
        """위 꼬리와 몸통 전체 범위에서 균등 분포 랜덤 샘플링을 수행합니다."""
        return random.uniform(*self.headbody())

    def bodytail_sample(self) -> float:
        """몸통과 아래 꼬리 전체 범위에서 균등 분포 랜덤 샘플링을 수행합니다."""
        return random.uniform(*self.bodytail())

