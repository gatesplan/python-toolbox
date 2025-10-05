from dataclasses import dataclass


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
