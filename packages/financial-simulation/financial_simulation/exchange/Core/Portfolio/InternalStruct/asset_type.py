"""자산 타입 정의."""

from enum import Enum


class AssetType(Enum):
    """자산 타입."""

    CURRENCY = "currency"  # Currency 잔고 (입출금으로 관리)
    POSITION = "position"  # Position (거래로 생성/소멸)
