from __future__ import annotations
from typing import Union
from simple_logger import logger


class Token:
    """
    거래 가능한 자산의 기본 단위.
    특정 심볼과 수량을 가지며, 같은 symbol끼리만 연산 가능합니다.

    내부적으로 fixed-point 방식(10^8 스케일)을 사용하여
    부동소수점 오차를 완전히 제거합니다.
    """

    # Fixed-point 스케일 팩터: 1.0 = 100,000,000
    SCALE_FACTOR = 100_000_000

    def __init__(self, symbol: str, amount: float):
        """Token 초기화.

        Args:
            symbol: 자산 식별자
            amount: 자산 수량 (float, 내부적으로 정수로 변환됨)
        """
        self._symbol = symbol
        # float를 fixed-point 정수로 변환 (반올림)
        self._amount_fixed = round(amount * self.SCALE_FACTOR)

    @classmethod
    def _from_fixed(cls, symbol: str, amount_fixed: int) -> Token:
        """Fixed-point 값으로 Token 생성 (내부용, Pair 등에서 사용).

        Args:
            symbol: 자산 식별자
            amount_fixed: fixed-point 정수 값

        Returns:
            새 Token 인스턴스
        """
        token = cls.__new__(cls)
        token._symbol = symbol
        token._amount_fixed = amount_fixed
        return token

    @property
    def symbol(self) -> str:
        """자산 식별자를 반환합니다."""
        return self._symbol

    @property
    def amount(self) -> float:
        """자산 수량을 반환합니다."""
        # fixed-point 정수를 float로 변환
        return self._amount_fixed / self.SCALE_FACTOR

    @property
    def amount_fixed(self) -> int:
        """내부 fixed-point 값 반환 (read-only, Pair 등 내부 사용)"""
        return self._amount_fixed

    def split_by_amount(self, amount: float) -> tuple[Token, Token]:
        """특정 금액으로 토큰 분할."""
        logger.debug(f"Token.split_by_amount 시작: symbol={self._symbol}, amount={self.amount}, split_amount={amount}")

        if amount < 0:
            logger.error(f"분할 금액이 음수: {amount}")
            raise ValueError("Split amount cannot be negative")

        # float를 fixed-point로 변환
        split_fixed = round(amount * self.SCALE_FACTOR)

        if split_fixed > self._amount_fixed:
            logger.error(f"분할 금액이 보유량 초과: split={amount}, total={self.amount}")
            raise ValueError(
                f"Split amount {amount} exceeds token amount {self.amount}"
            )

        # 정수 연산으로 정확히 분할
        reduced_fixed = self._amount_fixed - split_fixed

        logger.debug(f"Token.split_by_amount 완료: reduced={reduced_fixed/self.SCALE_FACTOR}, splitted={split_fixed/self.SCALE_FACTOR}")

        # 새 Token 생성 (내부 생성자 사용)
        reduced = Token.__new__(Token)
        reduced._symbol = self._symbol
        reduced._amount_fixed = reduced_fixed

        splitted = Token.__new__(Token)
        splitted._symbol = self._symbol
        splitted._amount_fixed = split_fixed

        return (reduced, splitted)

    def split_by_ratio(self, ratio: float) -> tuple[Token, Token]:
        """비율로 토큰 분할."""
        logger.debug(f"Token.split_by_ratio 시작: symbol={self._symbol}, amount={self.amount}, ratio={ratio}")

        if not 0 <= ratio <= 1:
            logger.error(f"비율이 범위를 벗어남: {ratio}")
            raise ValueError(f"Ratio must be between 0 and 1, got {ratio}")

        # 비율을 적용하여 정수로 반올림
        split_fixed = round(self._amount_fixed * ratio)

        # reduced는 원본에서 splitted를 뺀 값 (정확히 일치)
        reduced_fixed = self._amount_fixed - split_fixed

        logger.debug(f"Token.split_by_ratio 완료: reduced={reduced_fixed/self.SCALE_FACTOR}, splitted={split_fixed/self.SCALE_FACTOR}")

        # 새 Token 생성 (내부 생성자 사용)
        reduced = Token.__new__(Token)
        reduced._symbol = self._symbol
        reduced._amount_fixed = reduced_fixed

        splitted = Token.__new__(Token)
        splitted._symbol = self._symbol
        splitted._amount_fixed = split_fixed

        return (reduced, splitted)

    def _check_symbol_match(self, other: Token, operation: str) -> None:
        """다른 Token과 symbol 일치 확인."""
        if self._symbol != other._symbol:
            logger.error(f"Token symbol 불일치: {operation} 연산 실패 ({self._symbol} vs {other._symbol})")
            raise ValueError(
                f"Cannot {operation} tokens with different symbols: "
                f"{self._symbol} and {other._symbol}"
            )

    # 비교 연산자
    def __eq__(self, other: object) -> bool:
        """같은 symbol의 Token끼리 수량이 같은지 비교합니다."""
        if not isinstance(other, Token):
            return False
        if self._symbol != other._symbol:
            return False
        # 정수 비교로 정확함
        return self._amount_fixed == other._amount_fixed

    def __lt__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (작음)."""
        self._check_symbol_match(other, "compare")
        return self._amount_fixed < other._amount_fixed

    def __le__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (작거나 같음)."""
        self._check_symbol_match(other, "compare")
        return self._amount_fixed <= other._amount_fixed

    def __gt__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (큼)."""
        self._check_symbol_match(other, "compare")
        return self._amount_fixed > other._amount_fixed

    def __ge__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (크거나 같음)."""
        self._check_symbol_match(other, "compare")
        return self._amount_fixed >= other._amount_fixed

    # 산술 연산자
    def __add__(self, other: Token) -> Token:
        """같은 symbol의 Token끼리 덧셈."""
        self._check_symbol_match(other, "add")

        # 새 Token 생성 (내부 생성자 사용)
        result = Token.__new__(Token)
        result._symbol = self._symbol
        result._amount_fixed = self._amount_fixed + other._amount_fixed

        return result

    def __sub__(self, other: Token) -> Token:
        """같은 symbol의 Token끼리 뺄셈."""
        self._check_symbol_match(other, "subtract")

        # 새 Token 생성 (내부 생성자 사용)
        result = Token.__new__(Token)
        result._symbol = self._symbol
        result._amount_fixed = self._amount_fixed - other._amount_fixed

        return result

    def __mul__(self, scalar: Union[int, float]) -> Token:
        """Token에 스칼라 곱셈."""
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"Cannot multiply Token by {type(scalar).__name__}")

        # 새 Token 생성 (내부 생성자 사용)
        result = Token.__new__(Token)
        result._symbol = self._symbol
        # 스칼라 곱셈 후 반올림
        result._amount_fixed = round(self._amount_fixed * scalar)

        return result

    def __rmul__(self, scalar: Union[int, float]) -> Token:
        """스칼라에 Token을 곱합니다 (교환법칙)."""
        return self.__mul__(scalar)

    def __repr__(self) -> str:
        """Token의 문자열 표현을 반환합니다."""
        return f"Token(symbol={self._symbol!r}, amount={self.amount})"

    def __str__(self) -> str:
        """Token의 읽기 쉬운 문자열 표현을 반환합니다."""
        return f"{self.amount} {self._symbol}"
