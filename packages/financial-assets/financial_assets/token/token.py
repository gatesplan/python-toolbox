from __future__ import annotations
import math
from typing import Union
from simple_logger import logger


class Token:
    """
    거래 가능한 자산의 기본 단위.
    특정 심볼과 수량을 가지며, 같은 symbol끼리만 연산 가능합니다.
    """

    def __init__(self, symbol: str, amount: float, decimal: int = 8):
        """Token 초기화."""
        self._symbol = symbol
        self._decimal = decimal
        self._amount = round(amount, decimal)

    @property
    def symbol(self) -> str:
        """자산 식별자를 반환합니다."""
        return self._symbol

    @property
    def amount(self) -> float:
        """자산 수량을 반환합니다."""
        return self._amount

    @property
    def decimal(self) -> int:
        """소수점 정밀도를 반환합니다."""
        return self._decimal

    def round(self, n: int) -> Token:
        """수량을 반올림한 새 Token 반환."""
        return Token(symbol=self._symbol, amount=round(self._amount, n), decimal=n)

    def split_by_amount(self, amount: float) -> tuple[Token, Token]:
        """특정 금액으로 토큰 분할."""
        logger.debug(f"Token.split_by_amount 시작: symbol={self._symbol}, amount={self._amount}, split_amount={amount}")

        if amount < 0:
            logger.error(f"분할 금액이 음수: {amount}")
            raise ValueError("Split amount cannot be negative")
        if amount > self._amount:
            logger.error(f"분할 금액이 보유량 초과: split={amount}, total={self._amount}")
            raise ValueError(
                f"Split amount {amount} exceeds token amount {self._amount}"
            )

        # splitted를 올림 처리 (원본 decimal 사용)
        splitted_amount = math.ceil(amount * 10**self._decimal) / 10**self._decimal

        # splitted는 원본을 초과할 수 없음
        splitted_amount = min(splitted_amount, self._amount)

        # reduced는 원본 - splitted
        reduced_amount = self._amount - splitted_amount

        # 부동소수점 오차 조정
        reduced_amount, splitted_amount = self._adjust_split_error(
            reduced_amount, splitted_amount
        )

        logger.debug(f"Token.split_by_amount 완료: reduced={reduced_amount}, splitted={splitted_amount}")

        return (
            Token(symbol=self._symbol, amount=reduced_amount, decimal=self._decimal),
            Token(symbol=self._symbol, amount=splitted_amount, decimal=self._decimal),
        )

    def split_by_ratio(self, ratio: float) -> tuple[Token, Token]:
        """비율로 토큰 분할."""
        logger.debug(f"Token.split_by_ratio 시작: symbol={self._symbol}, amount={self._amount}, ratio={ratio}")

        if not 0 <= ratio <= 1:
            logger.error(f"비율이 범위를 벗어남: {ratio}")
            raise ValueError(f"Ratio must be between 0 and 1, got {ratio}")

        # splitted를 올림 처리 (원본 decimal 사용)
        splitted_amount = (
            math.ceil(self._amount * ratio * 10**self._decimal) / 10**self._decimal
        )

        # splitted는 원본을 초과할 수 없음
        splitted_amount = min(splitted_amount, self._amount)

        # reduced는 원본 - splitted
        reduced_amount = self._amount - splitted_amount

        # 부동소수점 오차 조정
        reduced_amount, splitted_amount = self._adjust_split_error(
            reduced_amount, splitted_amount
        )

        logger.debug(f"Token.split_by_ratio 완료: reduced={reduced_amount}, splitted={splitted_amount}")

        return (
            Token(symbol=self._symbol, amount=reduced_amount, decimal=self._decimal),
            Token(symbol=self._symbol, amount=splitted_amount, decimal=self._decimal),
        )

    def _check_symbol_match(self, other: Token, operation: str) -> None:
        """다른 Token과 symbol 일치 확인."""
        if self._symbol != other._symbol:
            logger.error(f"Token symbol 불일치: {operation} 연산 실패 ({self._symbol} vs {other._symbol})")
            raise ValueError(
                f"Cannot {operation} tokens with different symbols: "
                f"{self._symbol} and {other._symbol}"
            )

    def _adjust_split_error(
        self, reduced_amount: float, splitted_amount: float
    ) -> tuple[float, float]:
        """분할 후 부동소수점 오차 조정."""
        total = reduced_amount + splitted_amount
        if total < self._amount:
            # 부족분을 reduced에 추가
            reduced_amount += self._amount - total
        elif total > self._amount:
            # 넘치는 분량을 splitted에서 제거
            splitted_amount -= total - self._amount

        return reduced_amount, splitted_amount

    # 비교 연산자
    def __eq__(self, other: object) -> bool:
        """같은 symbol의 Token끼리 수량이 같은지 비교합니다."""
        if not isinstance(other, Token):
            return False
        if self._symbol != other._symbol:
            return False
        return self._amount == other._amount

    def __lt__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (작음)."""
        self._check_symbol_match(other, "compare")
        return self._amount < other._amount

    def __le__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (작거나 같음)."""
        self._check_symbol_match(other, "compare")
        return self._amount <= other._amount

    def __gt__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (큼)."""
        self._check_symbol_match(other, "compare")
        return self._amount > other._amount

    def __ge__(self, other: Token) -> bool:
        """같은 symbol의 Token끼리 수량을 비교합니다 (크거나 같음)."""
        self._check_symbol_match(other, "compare")
        return self._amount >= other._amount

    # 산술 연산자
    def __add__(self, other: Token) -> Token:
        """같은 symbol의 Token끼리 덧셈."""
        self._check_symbol_match(other, "add")
        max_decimal = max(self._decimal, other._decimal)
        return Token(
            symbol=self._symbol,
            amount=self._amount + other._amount,
            decimal=max_decimal,
        )

    def __sub__(self, other: Token) -> Token:
        """같은 symbol의 Token끼리 뺄셈."""
        self._check_symbol_match(other, "subtract")
        max_decimal = max(self._decimal, other._decimal)
        return Token(
            symbol=self._symbol,
            amount=self._amount - other._amount,
            decimal=max_decimal,
        )

    def __mul__(self, scalar: Union[int, float]) -> Token:
        """Token에 스칼라 곱셈."""
        if not isinstance(scalar, (int, float)):
            raise TypeError(f"Cannot multiply Token by {type(scalar).__name__}")
        return Token(
            symbol=self._symbol, amount=self._amount * scalar, decimal=self._decimal
        )

    def __rmul__(self, scalar: Union[int, float]) -> Token:
        """스칼라에 Token을 곱합니다 (교환법칙)."""
        return self.__mul__(scalar)

    def __repr__(self) -> str:
        """Token의 문자열 표현을 반환합니다."""
        return f"Token(symbol={self._symbol!r}, amount={self._amount})"

    def __str__(self) -> str:
        """Token의 읽기 쉬운 문자열 표현을 반환합니다."""
        return f"{self._amount} {self._symbol}"
