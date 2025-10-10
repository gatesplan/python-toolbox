from __future__ import annotations
import math
from typing import Union


class Token:
    """
    거래 가능한 자산을 표현하는 기본 단위.

    Token은 특정 심볼(symbol)과 수량(amount)을 가지며, 역할 중립적으로 설계됩니다.
    같은 symbol끼리만 연산 및 비교가 가능합니다.

    Attributes:
        symbol (str): 자산 식별자 (예: BTC, ETH, USD)
        amount (float): 자산 수량
        decimal (int): 소수점 정밀도 (기본값: 8)
    """

    def __init__(self, symbol: str, amount: float, decimal: int = 8):
        """
        Token 초기화.

        Args:
            symbol: 자산 식별자
            amount: 자산 수량 (decimal 자리로 자동 반올림됨)
            decimal: 소수점 정밀도 (기본값: 8)
        """
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
        """
        수량을 반올림한 새로운 Token을 반환합니다.
        decimal 정밀도도 n으로 변경됩니다.

        Args:
            n: 반올림할 소수점 자리수

        Returns:
            반올림된 수량과 decimal을 가진 새 Token
        """
        return Token(symbol=self._symbol, amount=round(self._amount, n), decimal=n)

    def split_by_amount(self, amount: float) -> tuple[Token, Token]:
        """
        특정 금액으로 토큰을 분할합니다.

        splitted는 올림 처리되고, reduced는 원본에서 splitted를 뺀 값입니다.
        이를 통해 reduced + splitted = 원본이 보장됩니다.
        decimal 정밀도는 원본 Token의 값을 승계합니다.

        Args:
            amount: 분할할 금액

        Returns:
            (reduced, splitted): reduced는 남은 금액, splitted는 분할된 금액

        Raises:
            ValueError: amount가 음수이거나 원본보다 클 때

        Examples:
            >>> token = Token(symbol="BTC", amount=1.0)
            >>> reduced, splitted = token.split_by_amount(0.3)
            >>> # reduced.amount + splitted.amount == 1.0
        """
        if amount < 0:
            raise ValueError("Split amount cannot be negative")
        if amount > self._amount:
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

        return (
            Token(symbol=self._symbol, amount=reduced_amount, decimal=self._decimal),
            Token(symbol=self._symbol, amount=splitted_amount, decimal=self._decimal),
        )

    def split_by_ratio(self, ratio: float) -> tuple[Token, Token]:
        """
        비율로 토큰을 분할합니다.

        splitted는 올림 처리되고, reduced는 원본에서 splitted를 뺀 값입니다.
        이를 통해 reduced + splitted = 원본이 보장됩니다.
        decimal 정밀도는 원본 Token의 값을 승계합니다.

        Args:
            ratio: 분할 비율 (0.0 ~ 1.0)

        Returns:
            (reduced, splitted): reduced는 남은 금액, splitted는 분할된 금액

        Raises:
            ValueError: ratio가 0~1 범위를 벗어날 때

        Examples:
            >>> token = Token(symbol="BTC", amount=1.0)
            >>> reduced, splitted = token.split_by_ratio(0.3)
            >>> # splitted.amount ≈ 0.3, reduced.amount ≈ 0.7
            >>> # reduced.amount + splitted.amount == 1.0
        """
        if not 0 <= ratio <= 1:
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

        return (
            Token(symbol=self._symbol, amount=reduced_amount, decimal=self._decimal),
            Token(symbol=self._symbol, amount=splitted_amount, decimal=self._decimal),
        )

    def _check_symbol_match(self, other: Token, operation: str) -> None:
        """
        다른 Token과 symbol이 일치하는지 확인합니다.

        Args:
            other: 비교할 Token
            operation: 수행하려는 연산 이름 (에러 메시지용)

        Raises:
            ValueError: symbol이 일치하지 않을 때
        """
        if self._symbol != other._symbol:
            raise ValueError(
                f"Cannot {operation} tokens with different symbols: "
                f"{self._symbol} and {other._symbol}"
            )

    def _adjust_split_error(
        self, reduced_amount: float, splitted_amount: float
    ) -> tuple[float, float]:
        """
        split 연산 후 부동소수점 오차를 조정합니다.

        총합이 원본과 일치하도록 reduced 또는 splitted를 조정합니다.
        - 부족분: reduced에 추가
        - 초과분: splitted에서 제거

        Args:
            reduced_amount: 남은 금액
            splitted_amount: 분할된 금액

        Returns:
            조정된 (reduced_amount, splitted_amount) 튜플
        """
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
        """
        같은 symbol의 Token끼리 덧셈을 수행합니다.
        결과의 decimal은 두 Token 중 더 높은 정밀도를 따릅니다.
        """
        self._check_symbol_match(other, "add")
        max_decimal = max(self._decimal, other._decimal)
        return Token(
            symbol=self._symbol,
            amount=self._amount + other._amount,
            decimal=max_decimal,
        )

    def __sub__(self, other: Token) -> Token:
        """
        같은 symbol의 Token끼리 뺄셈을 수행합니다.
        결과의 decimal은 두 Token 중 더 높은 정밀도를 따릅니다.
        """
        self._check_symbol_match(other, "subtract")
        max_decimal = max(self._decimal, other._decimal)
        return Token(
            symbol=self._symbol,
            amount=self._amount - other._amount,
            decimal=max_decimal,
        )

    def __mul__(self, scalar: Union[int, float]) -> Token:
        """
        Token에 스칼라를 곱합니다.
        결과의 decimal은 원본 Token의 값을 유지합니다.
        """
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
