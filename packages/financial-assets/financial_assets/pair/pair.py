from __future__ import annotations
from typing import Union
from ..token import Token
from ..symbol import Symbol
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
        self._symbol = Symbol(f"{asset.symbol}/{value.symbol}")

    @property
    def ticker(self) -> str:
        """티커 문자열을 반환합니다 (예: "BTC-USDT"). 하위 호환성 유지."""
        return self._symbol.to_dash()

    @property
    def symbol(self) -> Symbol:
        """Symbol 객체를 반환합니다."""
        return self._symbol

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
        logger.debug(f"Pair.split_by_asset_amount 시작: ticker={self.ticker}, asset={self._asset.amount}, split_amount={amount}")

        # asset을 분할
        reduced_asset, splitted_asset = self._asset.split_by_amount(amount)

        # value를 정수 비례로 분할 (float ratio 사용 안 함)
        if self._asset.amount_fixed == 0:
            # asset이 0이면 value도 0으로 분할
            splitted_value_fixed = 0
            reduced_value_fixed = self._value.amount_fixed
        else:
            # splitted_value = (total_value * splitted_asset) / total_asset (정수 나눗셈)
            splitted_value_fixed = (self._value.amount_fixed * splitted_asset.amount_fixed) // self._asset.amount_fixed
            reduced_value_fixed = self._value.amount_fixed - splitted_value_fixed

        # Token 생성
        reduced_value = Token._from_fixed(self._value.symbol, reduced_value_fixed)
        splitted_value = Token._from_fixed(self._value.symbol, splitted_value_fixed)

        logger.debug(f"Pair.split_by_asset_amount 완료: reduced_asset={reduced_asset.amount}, splitted_asset={splitted_asset.amount}")

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def split_by_value_amount(self, amount: float) -> tuple[Pair, Pair]:
        """value 수량 기준으로 Pair 분할."""
        logger.debug(f"Pair.split_by_value_amount 시작: ticker={self.ticker}, value={self._value.amount}, split_amount={amount}")

        # value를 분할
        reduced_value, splitted_value = self._value.split_by_amount(amount)

        # asset을 정수 비례로 분할 (float ratio 사용 안 함)
        if self._value.amount_fixed == 0:
            # value가 0이면 asset도 0으로 분할
            splitted_asset_fixed = 0
            reduced_asset_fixed = self._asset.amount_fixed
        else:
            # splitted_asset = (total_asset * splitted_value) / total_value (정수 나눗셈)
            splitted_asset_fixed = (self._asset.amount_fixed * splitted_value.amount_fixed) // self._value.amount_fixed
            reduced_asset_fixed = self._asset.amount_fixed - splitted_asset_fixed

        # Token 생성
        reduced_asset = Token._from_fixed(self._asset.symbol, reduced_asset_fixed)
        splitted_asset = Token._from_fixed(self._asset.symbol, splitted_asset_fixed)

        logger.debug(f"Pair.split_by_value_amount 완료: reduced_value={reduced_value.amount}, splitted_value={splitted_value.amount}")

        return (
            Pair(asset=reduced_asset, value=reduced_value),
            Pair(asset=splitted_asset, value=splitted_value),
        )

    def split_by_ratio(self, ratio: float) -> tuple[Pair, Pair]:
        """비율 기준으로 Pair 분할."""
        logger.debug(f"Pair.split_by_ratio 시작: ticker={self.ticker}, ratio={ratio}")

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
        if self._asset.amount_fixed == 0:
            raise ValueError("Cannot calculate mean_value: asset amount is zero")
        # 정수 나눗셈으로 더 정확한 결과
        return self._value.amount_fixed / self._asset.amount_fixed

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
