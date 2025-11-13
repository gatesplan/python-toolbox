"""자산 잠금 정보."""

from __future__ import annotations
from dataclasses import dataclass
from .asset_type import AssetType


@dataclass(frozen=True)
class Promise:
    """자산 잠금 정보 (불변)."""

    promise_id: str  # 잠금 식별자 (주문 ID)
    asset_type: AssetType  # 자산 타입 (CURRENCY or POSITION)
    identifier: str  # Currency symbol 또는 Position ticker
    amount: float  # 잠금 수량

    def __post_init__(self):
        """생성 후 검증."""
        if self.amount <= 0:
            raise ValueError(f"Amount must be positive: {self.amount}")
