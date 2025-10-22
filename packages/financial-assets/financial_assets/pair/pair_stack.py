from __future__ import annotations
from typing import Optional
from .pair import Pair
from ..token import Token
from simple_logger import logger


class PairStack:
    """
    평균 단가가 다른 Pair들을 레이어로 관리하는 스택.
    LIFO 방식으로 포지션을 추적합니다.
    """

    # 평단가 차이 임계값 (0.01%)
    MERGE_THRESHOLD = 0.0001

    def __init__(self, pairs: Optional[list[Pair]] = None):
        """PairStack 초기화."""
        self._pairs: list[Pair] = []
        self._asset_symbol: Optional[str] = None
        self._value_symbol: Optional[str] = None

        if pairs:
            for pair in pairs:
                self.append(pair)

    @property
    def ticker(self) -> str:
        """티커 문자열 반환."""
        if self.is_empty():
            raise ValueError("Cannot get ticker: stack is empty")

        return f"{self._asset_symbol}-{self._value_symbol}"

    def get_asset_token(self) -> Token:
        """전체 asset Token 반환."""
        if self.is_empty():
            raise ValueError("Cannot get asset token: stack is empty")

        return Token(symbol=self._asset_symbol, amount=self.total_asset_amount())

    def get_value_token(self) -> Token:
        """전체 value Token 반환."""
        if self.is_empty():
            raise ValueError("Cannot get value token: stack is empty")

        return Token(symbol=self._value_symbol, amount=self.total_value_amount())

    def get_asset(self) -> float:
        """전체 asset 수량 반환."""
        if self.is_empty():
            raise ValueError("Cannot get asset: stack is empty")

        return self.total_asset_amount()

    def get_value(self) -> float:
        """전체 value 수량 반환."""
        if self.is_empty():
            raise ValueError("Cannot get value: stack is empty")

        return self.total_value_amount()

    def append(self, pair: Pair) -> bool:
        """Pair를 스택에 추가하고 필요시 최상단 Pair와 병합."""
        logger.debug(f"PairStack.append 시작: pair={pair.ticker}, asset={pair.get_asset()}")

        # 빈 스택이면 symbol 설정
        if self.is_empty():
            self._asset_symbol = pair.get_asset_token().symbol
            self._value_symbol = pair.get_value_token().symbol
            self._pairs.append(pair)
            logger.debug("PairStack.append: 빈 스택에 첫 Pair 추가")
            return True

        # ticker 일치 검증
        if pair.get_asset_token().symbol != self._asset_symbol:
            logger.error(f"PairStack.append: asset symbol 불일치 ({pair.get_asset_token().symbol} vs {self._asset_symbol})")
            return False
        if pair.get_value_token().symbol != self._value_symbol:
            logger.error(f"PairStack.append: value symbol 불일치 ({pair.get_value_token().symbol} vs {self._value_symbol})")
            return False

        # 최상단 Pair와 평단가 비교
        top_pair = self._pairs[-1]

        # 둘 중 하나라도 asset amount가 0이면 병합 불가
        if top_pair.get_asset() == 0 or pair.get_asset() == 0:
            self._pairs.append(pair)
            return True

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
            logger.debug(f"PairStack.append: Pair 병합됨 (diff_ratio={diff_ratio:.6f})")
        else:
            self._pairs.append(pair)
            logger.debug(f"PairStack.append: 새 레이어 추가 (diff_ratio={diff_ratio:.6f})")

        return True

    def mean_value(self) -> float:
        """전체 스택의 평단가 반환."""
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
        """모든 Pair를 하나로 합산하여 단일 Pair 반환."""
        if self.is_empty():
            raise ValueError("Cannot flatten: stack is empty")

        result = self._pairs[0]
        for pair in self._pairs[1:]:
            result = result + pair
        return result

    def split_by_asset_amount(self, amount: float) -> PairStack:
        """asset 수량 기준으로 스택 분할."""
        logger.debug(f"PairStack.split_by_asset_amount 시작: total_asset={self.total_asset_amount()}, split_amount={amount}")

        if amount < 0:
            logger.error(f"분할 수량이 음수: {amount}")
            raise ValueError(f"Amount must be non-negative, got {amount}")

        total_asset = self.total_asset_amount()
        if total_asset == 0:
            logger.error("총 asset 수량이 0")
            raise RuntimeError("Cannot split: total asset amount is zero")

        if amount > total_asset:
            logger.error(f"분할 수량이 총량 초과: split={amount}, total={total_asset}")
            raise ValueError(
                f"Amount {amount} exceeds total asset amount {total_asset}"
            )

        ratio = amount / total_asset
        return self.split_by_ratio(ratio)

    def split_by_value_amount(self, amount: float) -> PairStack:
        """value 수량 기준으로 스택 분할."""
        logger.debug(f"PairStack.split_by_value_amount 시작: total_value={self.total_value_amount()}, split_amount={amount}")

        if amount < 0:
            logger.error(f"분할 수량이 음수: {amount}")
            raise ValueError(f"Amount must be non-negative, got {amount}")

        total_value = self.total_value_amount()
        if total_value == 0:
            logger.error("총 value 수량이 0")
            raise RuntimeError("Cannot split: total value amount is zero")

        if amount > total_value:
            logger.error(f"분할 수량이 총량 초과: split={amount}, total={total_value}")
            raise ValueError(
                f"Amount {amount} exceeds total value amount {total_value}"
            )

        ratio = amount / total_value
        return self.split_by_ratio(ratio)

    def split_by_ratio(self, ratio: float) -> PairStack:
        """비율 기준으로 스택 분할."""
        logger.debug(f"PairStack.split_by_ratio 시작: layers={len(self._pairs)}, ratio={ratio}")

        if not 0 <= ratio <= 1:
            logger.error(f"비율이 범위를 벗어남: {ratio}")
            raise ValueError(f"Ratio must be between 0 and 1, got {ratio}")

        if ratio == 0:
            return PairStack()

        if ratio == 1:
            splitted = PairStack(self._pairs.copy())
            self._pairs.clear()
            self._asset_symbol = None
            self._value_symbol = None
            return splitted

        total_value = self.total_value_amount()
        if total_value == 0:
            raise RuntimeError("Cannot split: total value amount is zero")

        target_value = total_value * ratio
        splitted_pairs: list[Pair] = []
        remaining_target = target_value

        # 스택 위(맨 뒤)부터 순서대로 value 기준으로 뽑기
        while remaining_target > 0 and self._pairs:
            current_pair = self._pairs[-1]
            current_value = current_pair.get_value()

            if current_value <= remaining_target:
                # 현재 Pair 전체를 가져감
                splitted_pairs.append(current_pair)
                remaining_target -= current_value
                self._pairs.pop()
            else:
                # 현재 Pair를 분할
                reduced, splitted = current_pair.split_by_value_amount(remaining_target)
                self._pairs[-1] = reduced
                splitted_pairs.append(splitted)
                remaining_target = 0

        # 스택이 비어있거나 남은 수량이 너무 작으면 정리 (garbage control)
        if self.is_empty() or self.total_value_amount() < 0.0001:
            self._pairs.clear()
            self._asset_symbol = None
            self._value_symbol = None

        logger.debug(f"PairStack.split_by_ratio 완료: splitted_layers={len(splitted_pairs)}, remaining_layers={len(self._pairs)}")

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

    def __eq__(self, other: object) -> bool:
        """PairStack 동등성 비교."""
        if not isinstance(other, PairStack):
            return False

        # 둘 다 비어있으면 같음
        if self.is_empty() and other.is_empty():
            return True

        # 하나만 비어있으면 다름
        if self.is_empty() or other.is_empty():
            return False

        # symbol 비교
        return (
            self._asset_symbol == other._asset_symbol
            and self._value_symbol == other._value_symbol
        )
