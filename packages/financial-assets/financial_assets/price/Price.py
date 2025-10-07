from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Price:
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
        """몸통 상단"""
        return max(self.o, self.c)

    def bodybottom(self) -> float:
        """몸통 하단"""
        return min(self.o, self.c)

    ########## ########## 범위 반환 메서드 ########## ##########
    def body(self) -> tuple[float, float]:
        """몸통 범위 (min, max)"""
        return (self.bodybottom(), self.bodytop())

    def head(self) -> tuple[float, float]:
        """위 꼬리 범위 (min, max)"""
        return (self.bodytop(), self.h)

    def tail(self) -> tuple[float, float]:
        """아래 꼬리 범위 (min, max)"""
        return (self.l, self.bodybottom())

    def headbody(self) -> tuple[float, float]:
        """위 꼬리 + 몸통 범위 (min, max)"""
        return (self.bodybottom(), self.h)

    def bodytail(self) -> tuple[float, float]:
        """몸통 + 아래 꼬리 범위 (min, max)"""
        return (self.l, self.bodytop())

    ########## ########## 샘플링 메서드 ########## ##########
    def head_sample(self) -> float:
        """위 꼬리 범위에서 랜덤 샘플"""
        return random.uniform(*self.head())

    def tail_sample(self) -> float:
        """아래 꼬리 범위에서 랜덤 샘플"""
        return random.uniform(*self.tail())

    def body_sample(self) -> float:
        """몸통 범위에서 랜덤 샘플"""
        return random.uniform(*self.body())

    def headbody_sample(self) -> float:
        """위 꼬리 + 몸통 범위에서 랜덤 샘플"""
        return random.uniform(*self.headbody())

    def bodytail_sample(self) -> float:
        """몸통 + 아래 꼬리 범위에서 랜덤 샘플"""
        return random.uniform(*self.bodytail())

