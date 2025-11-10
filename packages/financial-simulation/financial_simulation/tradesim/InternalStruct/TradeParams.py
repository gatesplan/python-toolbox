# Worker가 반환하는 체결 파라미터

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TradeParams:
    fill_amount: float  # 체결 수량
    fill_price: float   # 체결 가격
    fill_index: int     # 체결 인덱스 (1부터 시작)
