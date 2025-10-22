"""CalculationTool - 시뮬레이션 수치 계산 유틸리티."""

from __future__ import annotations
from typing import List
import numpy as np


class CalculationTool:
    """
    시뮬레이션에 필요한 수치 계산을 제공하는 도구 클래스.

    모든 메서드는 stateless하며 순수 함수입니다.
    """

    def round_to_min_amount(self, amount: float, min_amount: float) -> float:
        """
        금액을 최소 거래 단위의 배수로 내림.

        Args:
            amount: 반올림할 금액
            min_amount: 최소 거래 단위

        Returns:
            float: min_amount의 배수로 내림된 금액

        Example:
            >>> calc = CalculationTool()
            >>> calc.round_to_min_amount(1.234, 0.01)
            1.23
        """
        if amount <= 0:
            return 0.0

        return (amount // min_amount) * min_amount

    def get_price_sample(
        self,
        min: float,
        max: float,
        mean: float,
        std: float,
        min_z: float = -2.0,
        max_z: float = 2.0,
    ) -> float:
        """
        정규분포에서 가격을 샘플링하고 범위 내로 클리핑.

        Args:
            min: 최소 가격
            max: 최대 가격
            mean: 정규분포 평균
            std: 정규분포 표준편차
            min_z: 최소 z-score (기본값: -2.0)
            max_z: 최대 z-score (기본값: 2.0)

        Returns:
            float: [min, max] 범위 내의 샘플링된 가격

        Example:
            >>> calc = CalculationTool()
            >>> price = calc.get_price_sample(100, 110, 105, 2)
            >>> assert 100 <= price <= 110
        """
        # 정규분포에서 샘플링
        z_score = np.random.normal(0, 1)

        # z-score 클리핑
        z_score = np.clip(z_score, min_z, max_z)

        # 가격 계산
        price = mean + z_score * std

        # 최종 범위 클리핑
        return np.clip(price, min, max)

    def get_separated_amount_sequence(
        self,
        base: float,
        min_trade_amount: float,
        split_to: int,
    ) -> List[float]:
        """
        금액을 랜덤하게 여러 조각으로 분할.

        각 조각은 min_trade_amount의 배수이며, 합은 정확히 base입니다.

        Args:
            base: 분할할 총 금액
            min_trade_amount: 최소 거래 단위
            split_to: 분할할 조각 개수

        Returns:
            List[float]: split_to 개의 금액 리스트

        Example:
            >>> calc = CalculationTool()
            >>> pieces = calc.get_separated_amount_sequence(10.0, 0.1, 3)
            >>> assert len(pieces) == 3
            >>> assert sum(pieces) == 10.0
        """
        if split_to == 1:
            return [base]

        # Dirichlet 분포로 비율 생성 (균등 분포)
        alphas = np.ones(split_to)
        ratios = np.random.dirichlet(alphas)

        # 각 조각에 비율 적용
        raw_pieces = ratios * base

        # 각 조각을 최소 거래 단위로 내림
        rounded_pieces = [
            self.round_to_min_amount(piece, min_trade_amount)
            for piece in raw_pieces
        ]

        # 반올림으로 인한 잔여량 계산
        remainder = base - sum(rounded_pieces)

        # 마지막 조각에 잔여량 추가
        rounded_pieces[-1] += remainder

        return rounded_pieces
