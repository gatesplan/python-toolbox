from __future__ import annotations
from typing import Union
from ..token import Token
from simple_logger import logger


class Pair:
    """
    자산(asset)과 가치(value)의 쌍을 표현하는 기본 단위.
    같은 symbol 쌍끼리만 연산 가능합니다.
    """

    def __init__(self, asset: Token, value: Token):
        """Pair 초기화."""
        self._asset = asset
        self._value = value
        self._ticker = f"{asset.symbol}-{value.symbol}"

    @property
    def ticker(self) -> str:
        """티커 문자열을 반환합니다 (예: "BTC-USD")."""
        return self._ticker

    def get_asset_token(self) -> Token:
        """거래 대상 자산 Token 반환."""
        return self._asset

    def get_value_token(self) -> Token:
        """자산의 교환 가치 Token 반환."""
        return self._value

    def get_asset(self) -> float:
        """거래 대상 자산 수량 반환."""
        return self._asset.amount

    def get_value(self) -> float:
        """자산의 교환 가치 수량 반환."""
        return self._value.amount

    def split_by_asset_amount(self, amount: float) -> tuple[Pair, Pair]:
        """asset 수량 기준으로 Pair 분할."""
        logger.debug(f"Pair.split_by_asset_amount 시작: ticker={self._ticker}, asset={self._asset.amount}, split_amount={amount}")

        # asset을 분할
        reduced_asset, splitted_asset = self._asset.split_by_amount(amount)

        # asset 분할 비율 계산
        if self._asset.amount == 0:
            ratio = 0.0
        else:
            ratio = splitted_asset.amount / self._asset.amount

        # value를 같은 비율로 분할
        reduced_value, splitted_value = self._value.split_by_ratio(ratio)

        logger.debug(f"Pair.split_by_asset_amount 완료: reduced_asset={reduced_asset.amount}, splitted_asset={splitted_asset.amount}")

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def split_by_value_amount(self, amount: float) -> tuple[Pair, Pair]:
        """value 수량 기준으로 Pair 분할."""
        logger.debug(f"Pair.split_by_value_amount 시작: ticker={self._ticker}, value={self._value.amount}, split_amount={amount}")

        # value를 분할
        reduced_value, splitted_value = self._value.split_by_amount(amount)

        # value 분할 비율 계산
        if self._value.amount == 0:
            ratio = 0.0
        else:
            ratio = splitted_value.amount / self._value.amount

        # asset을 같은 비율로 분할
        reduced_asset, splitted_asset = self._asset.split_by_ratio(ratio)

        logger.debug(f"Pair.split_by_value_amount 완료: reduced_value={reduced_value.amount}, splitted_value={splitted_value.amount}")

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def split_by_ratio(self, ratio: float) -> tuple[Pair, Pair]:
        """비율 기준으로 Pair 분할."""
        logger.debug(f"Pair.split_by_ratio 시작: ticker={self._ticker}, ratio={ratio}")

        # asset과 value를 같은 비율로 분할
        reduced_asset, splitted_asset = self._asset.split_by_ratio(ratio)
        reduced_value, splitted_value = self._value.split_by_ratio(ratio)

        logger.debug(f"Pair.split_by_ratio 완료: reduced_asset={reduced_asset.amount}, splitted_asset={splitted_asset.amount}")

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def mean_value(self) -> float:
        """단위 asset당 평균 가치 계산."""
        if self._asset.amount == 0:
            raise ValueError("Cannot calculate mean_value: asset amount is zero")
        return self._value.amount / self._asset.amount

    def _check_pair_match(self, other: Pair, operation: str) -> None:
        """다른 Pair와 symbol 일치 여부 확인."""
        if self._asset.symbol != other._asset.symbol:
            logger.error(f"Pair asset symbol 불일치: {operation} 연산 실패 ({self._asset.symbol} vs {other._asset.symbol})")
            raise ValueError(
                f"Cannot {operation} pairs with different asset symbols: "
                f"{self._asset.symbol} and {other._asset.symbol}"
            )
        if self._value.symbol != other._value.symbol:
            logger.error(f"Pair value symbol 불일치: {operation} 연산 실패 ({self._value.symbol} vs {other._value.symbol})")
            raise ValueError(
                f"Cannot {operation} pairs with different value symbols: "
                f"{self._value.symbol} and {other._value.symbol}"
            )

    # 비교 연산자
    def __eq__(self, other: object) -> bool:
        """같은 symbol 쌍의 Pair끼리 동등성 비교."""
        if not isinstance(other, Pair):
            return False
        return self._asset == other._asset and self._value == other._value

    # 산술 연산자
    def __add__(self, other: Pair) -> Pair:
        """같은 symbol 쌍의 Pair끼리 덧셈 수행."""
        self._check_pair_match(other, "add")
        return Pair(asset=self._asset + other._asset, value=self._value + other._value)

    def __sub__(self, other: Pair) -> Pair:
        """같은 symbol 쌍의 Pair끼리 뺄셈 수행."""
        self._check_pair_match(other, "subtract")
        return Pair(asset=self._asset - other._asset, value=self._value - other._value)

    def __mul__(self, scalar: Union[int, float]) -> Pair:
        """Pair에 스칼라 곱셈."""
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"Cannot multiply Pair by {type(scalar).__name__}")
        return Pair(asset=self._asset * scalar, value=self._value * scalar)

    def __rmul__(self, scalar: Union[int, float]) -> Pair:
        """스칼라에 Pair를 곱합니다 (교환법칙)."""
        return self.__mul__(scalar)

    def __repr__(self) -> str:
        """Pair의 문자열 표현을 반환합니다."""
        return f"Pair(asset={self._asset!r}, value={self._value!r})"

    def __str__(self) -> str:
        """Pair의 읽기 쉬운 문자열 표현을 반환합니다."""
        return f"{self._asset} ≈ {self._value}"
