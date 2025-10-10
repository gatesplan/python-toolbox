from __future__ import annotations
from typing import Union
from ..token import Token


class Pair:
    """
    자산(asset)과 가치(value)의 쌍을 표현하는 기본 단위.

    Pair는 거래 대상 자산(asset)과 그 교환 가치(value)를 함께 관리합니다.
    같은 symbol 쌍끼리만 연산 및 비교가 가능합니다.

    Attributes:
        asset (Token): 거래 대상 자산
        value (Token): 자산의 교환 가치
    """

    def __init__(self, asset: Token, value: Token):
        """
        Pair 초기화.

        Args:
            asset: 거래 대상 자산 Token
            value: 자산의 교환 가치 Token
        """
        self._asset = asset
        self._value = value
        self._ticker = f"{asset.symbol}-{value.symbol}"

    @property
    def ticker(self) -> str:
        """티커 문자열을 반환합니다 (예: "BTC-USD")."""
        return self._ticker

    def get_asset_token(self) -> Token:
        """거래 대상 자산 Token을 반환합니다."""
        return self._asset

    def get_value_token(self) -> Token:
        """자산의 교환 가치 Token을 반환합니다."""
        return self._value

    def get_asset(self) -> float:
        """거래 대상 자산의 수량을 반환합니다."""
        return self._asset.amount

    def get_value(self) -> float:
        """자산의 교환 가치 수량을 반환합니다."""
        return self._value.amount

    def split_by_asset_amount(self, amount: float) -> tuple[Pair, Pair]:
        """
        asset 수량 기준으로 Pair를 분할합니다.

        asset의 비율에 따라 value도 비례적으로 분할됩니다.

        Args:
            amount: 분할할 asset 수량

        Returns:
            (reduced, splitted): reduced는 남은 Pair, splitted는 분할된 Pair

        Raises:
            ValueError: amount가 음수이거나 asset 수량을 초과할 때

        Examples:
            >>> asset = Token(symbol="BTC", amount=1.0)
            >>> value = Token(symbol="USD", amount=50000.0)
            >>> pair = Pair(asset=asset, value=value)
            >>> reduced, splitted = pair.split_by_asset_amount(0.3)
            >>> # reduced: 0.7 BTC worth $35,000
            >>> # splitted: 0.3 BTC worth $15,000
        """
        # asset을 분할
        reduced_asset, splitted_asset = self._asset.split_by_amount(amount)

        # asset 분할 비율 계산
        if self._asset.amount == 0:
            ratio = 0.0
        else:
            ratio = splitted_asset.amount / self._asset.amount

        # value를 같은 비율로 분할
        reduced_value, splitted_value = self._value.split_by_ratio(ratio)

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def split_by_value_amount(self, amount: float) -> tuple[Pair, Pair]:
        """
        value 수량 기준으로 Pair를 분할합니다.

        value의 비율에 따라 asset도 비례적으로 분할됩니다.

        Args:
            amount: 분할할 value 수량

        Returns:
            (reduced, splitted): reduced는 남은 Pair, splitted는 분할된 Pair

        Raises:
            ValueError: amount가 음수이거나 value 수량을 초과할 때

        Examples:
            >>> asset = Token(symbol="BTC", amount=1.0)
            >>> value = Token(symbol="USD", amount=50000.0)
            >>> pair = Pair(asset=asset, value=value)
            >>> reduced, splitted = pair.split_by_value_amount(15000.0)
            >>> # reduced: 0.7 BTC worth $35,000
            >>> # splitted: 0.3 BTC worth $15,000
        """
        # value를 분할
        reduced_value, splitted_value = self._value.split_by_amount(amount)

        # value 분할 비율 계산
        if self._value.amount == 0:
            ratio = 0.0
        else:
            ratio = splitted_value.amount / self._value.amount

        # asset을 같은 비율로 분할
        reduced_asset, splitted_asset = self._asset.split_by_ratio(ratio)

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def split_by_ratio(self, ratio: float) -> tuple[Pair, Pair]:
        """
        비율로 Pair를 분할합니다.

        asset과 value 모두 같은 비율로 분할됩니다.

        Args:
            ratio: 분할 비율 (0.0 ~ 1.0)

        Returns:
            (reduced, splitted): reduced는 남은 Pair, splitted는 분할된 Pair

        Raises:
            ValueError: ratio가 0~1 범위를 벗어날 때

        Examples:
            >>> asset = Token(symbol="BTC", amount=1.0)
            >>> value = Token(symbol="USD", amount=50000.0)
            >>> pair = Pair(asset=asset, value=value)
            >>> reduced, splitted = pair.split_by_ratio(0.3)
            >>> # reduced: 0.7 BTC worth $35,000
            >>> # splitted: 0.3 BTC worth $15,000
        """
        # asset과 value를 같은 비율로 분할
        reduced_asset, splitted_asset = self._asset.split_by_ratio(ratio)
        reduced_value, splitted_value = self._value.split_by_ratio(ratio)

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def mean_value(self) -> float:
        """
        단위 asset당 평균 value를 반환합니다.

        Returns:
            float: value.amount / asset.amount (단위당 가격)

        Raises:
            ValueError: asset.amount가 0일 때

        Examples:
            >>> pair = Pair(
            ...     asset=Token(symbol="BTC", amount=1.5),
            ...     value=Token(symbol="USD", amount=75000.0)
            ... )
            >>> pair.mean_value()
            50000.0  # $50,000 per BTC
        """
        if self._asset.amount == 0:
            raise ValueError("Cannot calculate mean_value: asset amount is zero")
        return self._value.amount / self._asset.amount

    def _check_pair_match(self, other: Pair, operation: str) -> None:
        """
        다른 Pair와 asset, value symbol이 일치하는지 확인합니다.

        Args:
            other: 비교할 Pair
            operation: 수행하려는 연산 이름 (에러 메시지용)

        Raises:
            ValueError: asset 또는 value symbol이 일치하지 않을 때
        """
        if self._asset.symbol != other._asset.symbol:
            raise ValueError(
                f"Cannot {operation} pairs with different asset symbols: "
                f"{self._asset.symbol} and {other._asset.symbol}"
            )
        if self._value.symbol != other._value.symbol:
            raise ValueError(
                f"Cannot {operation} pairs with different value symbols: "
                f"{self._value.symbol} and {other._value.symbol}"
            )

    # 비교 연산자
    def __eq__(self, other: object) -> bool:
        """
        같은 symbol 쌍의 Pair끼리 asset와 value가 모두 같은지 비교합니다.
        """
        if not isinstance(other, Pair):
            return False
        return self._asset == other._asset and self._value == other._value

    # 산술 연산자
    def __add__(self, other: Pair) -> Pair:
        """
        같은 symbol 쌍의 Pair끼리 덧셈을 수행합니다.
        """
        self._check_pair_match(other, "add")
        return Pair(asset=self._asset + other._asset, value=self._value + other._value)

    def __sub__(self, other: Pair) -> Pair:
        """
        같은 symbol 쌍의 Pair끼리 뺄셈을 수행합니다.
        """
        self._check_pair_match(other, "subtract")
        return Pair(asset=self._asset - other._asset, value=self._value - other._value)

    def __mul__(self, scalar: Union[int, float]) -> Pair:
        """
        Pair에 스칼라를 곱합니다.
        """
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
