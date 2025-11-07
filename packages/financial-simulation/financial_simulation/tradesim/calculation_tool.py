"""CalculationTool - 시뮬레이션 수치 계산 유틸리티."""

from __future__ import annotations
from typing import List
import numpy as np


class CalculationTool:
    """시뮬레이션 수치 계산 도구 (stateless static 메서드)."""

    @staticmethod
    def round_to_min_amount(amount: float, min_amount: float) -> float:
        """금액을 최소 거래 단위의 배수로 내림."""
        if amount <= 0:
            return 0.0

        return (amount // min_amount) * min_amount

    @staticmethod
    def get_price_sample(
        min: float,
        max: float,
        mean: float,
        std: float,
        min_z: float = -2.0,
        max_z: float = 2.0,
    ) -> float:
        """정규분포 기반 가격 샘플링 (범위 클리핑 적용)."""
        # 정규분포에서 샘플링
        z_score = np.random.normal(0, 1)

        # z-score 클리핑
        z_score = np.clip(z_score, min_z, max_z)

        # 가격 계산
        price = mean + z_score * std

        # 최종 범위 클리핑
        return np.clip(price, min, max)

    @staticmethod
    def get_separated_amount_sequence(
        base: float,
        min_trade_amount: float,
        split_to: int,
    ) -> List[float]:
        """금액을 랜덤하게 여러 조각으로 분할."""
        if split_to == 1:
            return [base]

        # Dirichlet 분포로 비율 생성 (균등 분포)
        alphas = np.ones(split_to)
        ratios = np.random.dirichlet(alphas)

        # 각 조각에 비율 적용
        raw_pieces = ratios * base

        # 각 조각을 최소 거래 단위로 내림
        rounded_pieces = [
            CalculationTool.round_to_min_amount(piece, min_trade_amount)
            for piece in raw_pieces
        ]

        # 반올림으로 인한 잔여량 계산
        remainder = base - sum(rounded_pieces)

        # 마지막 조각에 잔여량 추가
        rounded_pieces[-1] += remainder

        return rounded_pieces

    @staticmethod
    def get_price_range(price, target_price: float) -> str:
        """target_price가 캔들의 어느 범위에 위치하는지 판단."""
        body_bottom = price.bodybottom()
        body_top = price.bodytop()

        # Body 범위 확인
        if body_bottom <= target_price <= body_top:
            return "body"

        # Head 범위 확인 (위쪽 꼬리)
        if body_top < target_price <= price.h:
            return "head"

        # Tail 범위 확인 (아래쪽 꼬리)
        if price.l <= target_price < body_bottom:
            return "tail"

        # 범위 밖
        return "none"
