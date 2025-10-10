from __future__ import annotations
from typing import Optional
from .pair import Pair
from ..token import Token


class PairStack:
    """
    같은 ticker(symbol pair)의 Pair들을 스택으로 관리.

    평단가가 유사한(0.01% 이내) Pair는 자동으로 병합됩니다.
    하나의 Pair처럼 동작하지만, 내부적으로는 여러 레이어로 관리됩니다.

    Attributes:
        _pairs (list[Pair]): Pair들의 스택
        _asset_symbol (str | None): 관리하는 asset symbol
        _value_symbol (str | None): 관리하는 value symbol
    """

    # 평단가 차이 임계값 (0.01%)
    MERGE_THRESHOLD = 0.0001

    def __init__(self, pairs: Optional[list[Pair]] = None):
        """
        PairStack 초기화.

        Args:
            pairs: 초기 Pair 리스트 (선택, 자동 병합 적용됨)
        """
        self._pairs: list[Pair] = []
        self._asset_symbol: Optional[str] = None
        self._value_symbol: Optional[str] = None

        if pairs:
            for pair in pairs:
                self.append(pair)

    @property
    def ticker(self) -> str:
        """
        티커 문자열을 반환합니다 (예: "BTC-USD").

        Returns:
            str: 티커 문자열

        Raises:
            ValueError: 스택이 비어있을 때
        """
        if self.is_empty():
            raise ValueError("Cannot get ticker: stack is empty")

        return f"{self._asset_symbol}-{self._value_symbol}"

    def get_asset_token(self) -> Token:
        """
        전체 asset을 하나의 Token으로 반환합니다.

        Returns:
            Token: 총 asset 수량의 Token

        Raises:
            ValueError: 스택이 비어있을 때
        """
        if self.is_empty():
            raise ValueError("Cannot get asset token: stack is empty")

        return Token(symbol=self._asset_symbol, amount=self.total_asset_amount())

    def get_value_token(self) -> Token:
        """
        전체 value를 하나의 Token으로 반환합니다.

        Returns:
            Token: 총 value 수량의 Token

        Raises:
            ValueError: 스택이 비어있을 때
        """
        if self.is_empty():
            raise ValueError("Cannot get value token: stack is empty")

        return Token(symbol=self._value_symbol, amount=self.total_value_amount())

    def get_asset(self) -> float:
        """
        전체 asset 수량을 반환합니다.

        Returns:
            float: 총 asset 수량

        Raises:
            ValueError: 스택이 비어있을 때
        """
        if self.is_empty():
            raise ValueError("Cannot get asset: stack is empty")

        return self.total_asset_amount()

    def get_value(self) -> float:
        """
        전체 value 수량을 반환합니다.

        Returns:
            float: 총 value 수량

        Raises:
            ValueError: 스택이 비어있을 때
        """
        if self.is_empty():
            raise ValueError("Cannot get value: stack is empty")

        return self.total_value_amount()

    def append(self, pair: Pair) -> None:
        """
        Pair를 스택에 추가.

        최상단 Pair와 평단가 차이가 0.01% 이내면 자동으로 병합됩니다.

        Args:
            pair: 추가할 Pair

        Raises:
            ValueError: 다른 ticker의 Pair를 추가하려고 할 때
        """
        # 빈 스택이면 symbol 설정
        if self.is_empty():
            self._asset_symbol = pair.get_asset_token().symbol
            self._value_symbol = pair.get_value_token().symbol
            self._pairs.append(pair)
            return

        # ticker 일치 검증
        if pair.get_asset_token().symbol != self._asset_symbol:
            raise ValueError(
                f"Cannot add pair with different asset symbol: "
                f"expected {self._asset_symbol}, got {pair.get_asset_token().symbol}"
            )
        if pair.get_value_token().symbol != self._value_symbol:
            raise ValueError(
                f"Cannot add pair with different value symbol: "
                f"expected {self._value_symbol}, got {pair.get_value_token().symbol}"
            )

        # 최상단 Pair와 평단가 비교
        top_pair = self._pairs[-1]

        # 둘 중 하나라도 asset amount가 0이면 병합 불가
        if top_pair.get_asset() == 0 or pair.get_asset() == 0:
            self._pairs.append(pair)
            return

        top_mean = top_pair.mean_value()
        new_mean = pair.mean_value()

        # 평단가 차이 계산
        if top_mean == 0:
            diff_ratio = 0.0 if new_mean == 0 else float('inf')
        else:
            diff_ratio = abs(new_mean - top_mean) / top_mean

        # 0.01% 이내면 병합
        if diff_ratio <= self.MERGE_THRESHOLD:
            merged = top_pair + pair
            self._pairs[-1] = merged
        else:
            self._pairs.append(pair)

    def mean_value(self) -> float:
        """
        전체 스택의 평단가 반환.

        Returns:
            float: 전체 value 합계 / 전체 asset 합계

        Raises:
            ValueError: 스택이 비어있거나 총 asset amount가 0일 때
        """
        if self.is_empty():
            raise ValueError("Cannot calculate mean_value: stack is empty")

        total_asset = self.total_asset_amount()
        if total_asset == 0:
            raise ValueError("Cannot calculate mean_value: total asset amount is zero")

        total_value = self.total_value_amount()
        return total_value / total_asset

    def total_asset_amount(self) -> float:
        """전체 asset 수량 합계 반환."""
        return sum(pair.get_asset() for pair in self._pairs)

    def total_value_amount(self) -> float:
        """전체 value 수량 합계 반환."""
        return sum(pair.get_value() for pair in self._pairs)

    def flatten(self) -> Pair:
        """
        모든 Pair를 하나로 합산하여 단일 Pair 반환.

        Returns:
            Pair: 합산된 단일 Pair

        Raises:
            ValueError: 스택이 비어있을 때
        """
        if self.is_empty():
            raise ValueError("Cannot flatten: stack is empty")

        result = self._pairs[0]
        for pair in self._pairs[1:]:
            result = result + pair
        return result

    def split_by_asset_amount(self, amount: float) -> PairStack:
        """
        asset 수량 기준으로 분할. 원본 수정, 분리된 PairStack 반환.

        스택 순서대로(맨 위부터) 분리합니다.

        Args:
            amount: 분리할 asset 수량

        Returns:
            PairStack: 분리된 PairStack (스택 순서 유지)

        Raises:
            ValueError: amount가 음수이거나 총 asset 수량을 초과할 때
        """
        if amount < 0:
            raise ValueError(f"Amount must be non-negative, got {amount}")

        total_asset = self.total_asset_amount()
        if amount > total_asset:
            raise ValueError(
                f"Amount {amount} exceeds total asset amount {total_asset}"
            )

        splitted_pairs: list[Pair] = []
        remaining_amount = amount

        # 스택 맨 위(index 0)부터 순서대로 분리
        while remaining_amount > 0 and self._pairs:
            current_pair = self._pairs[0]

            if current_pair.get_asset() <= remaining_amount:
                # 현재 Pair 전체를 가져감
                splitted_pairs.append(current_pair)
                remaining_amount -= current_pair.get_asset()
                self._pairs.pop(0)
            else:
                # 현재 Pair를 분할
                reduced, splitted = current_pair.split_by_asset_amount(remaining_amount)
                self._pairs[0] = reduced
                splitted_pairs.append(splitted)
                remaining_amount = 0

        # 스택이 비어있으면 symbol 초기화
        if self.is_empty():
            self._asset_symbol = None
            self._value_symbol = None

        return PairStack(splitted_pairs)

    def split_by_value_amount(self, amount: float) -> PairStack:
        """
        value 수량 기준으로 분할. 원본 수정, 분리된 PairStack 반환.

        스택 순서대로(맨 위부터) 분리합니다.

        Args:
            amount: 분리할 value 수량

        Returns:
            PairStack: 분리된 PairStack (스택 순서 유지)

        Raises:
            ValueError: amount가 음수이거나 총 value 수량을 초과할 때
        """
        if amount < 0:
            raise ValueError(f"Amount must be non-negative, got {amount}")

        total_value = self.total_value_amount()
        if amount > total_value:
            raise ValueError(
                f"Amount {amount} exceeds total value amount {total_value}"
            )

        splitted_pairs: list[Pair] = []
        remaining_amount = amount

        # 스택 맨 위(index 0)부터 순서대로 분리
        while remaining_amount > 0 and self._pairs:
            current_pair = self._pairs[0]

            if current_pair.get_value() <= remaining_amount:
                # 현재 Pair 전체를 가져감
                splitted_pairs.append(current_pair)
                remaining_amount -= current_pair.get_value()
                self._pairs.pop(0)
            else:
                # 현재 Pair를 분할
                reduced, splitted = current_pair.split_by_value_amount(remaining_amount)
                self._pairs[0] = reduced
                splitted_pairs.append(splitted)
                remaining_amount = 0

        # 스택이 비어있으면 symbol 초기화
        if self.is_empty():
            self._asset_symbol = None
            self._value_symbol = None

        return PairStack(splitted_pairs)

    def split_by_ratio(self, ratio: float) -> PairStack:
        """
        비율 기준으로 분할. 원본 수정, 분리된 PairStack 반환.

        모든 레이어를 같은 비율로 분할합니다.

        Args:
            ratio: 분할 비율 (0.0 ~ 1.0)

        Returns:
            PairStack: 분리된 PairStack (스택 순서 유지)

        Raises:
            ValueError: ratio가 0~1 범위를 벗어날 때
        """
        if not 0 <= ratio <= 1:
            raise ValueError(f"Ratio must be between 0 and 1, got {ratio}")

        if ratio == 0:
            return PairStack()

        if ratio == 1:
            splitted = PairStack(self._pairs.copy())
            self._pairs.clear()
            self._asset_symbol = None
            self._value_symbol = None
            return splitted

        splitted_pairs: list[Pair] = []
        new_pairs: list[Pair] = []

        # 각 레이어를 같은 비율로 분할
        for pair in self._pairs:
            reduced, splitted = pair.split_by_ratio(ratio)
            new_pairs.append(reduced)
            splitted_pairs.append(splitted)

        self._pairs = new_pairs
        return PairStack(splitted_pairs)

    def is_empty(self) -> bool:
        """스택이 비어있는지 확인."""
        return len(self._pairs) == 0

    def __len__(self) -> int:
        """스택에 있는 Pair 레이어 개수 반환."""
        return len(self._pairs)

    def __repr__(self) -> str:
        """PairStack의 문자열 표현 반환."""
        return f"PairStack(pairs={self._pairs!r})"

    def __str__(self) -> str:
        """PairStack의 읽기 쉬운 문자열 표현 반환."""
        if self.is_empty():
            return "PairStack(empty)"

        layers = "\n  ".join(str(pair) for pair in self._pairs)
        return f"PairStack({len(self)} layers):\n  {layers}"
