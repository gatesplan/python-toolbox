# 수량 분할

from __future__ import annotations
from typing import List
import numpy as np
from simple_logger import func_logging
from ..MathUtils.MathUtils import MathUtils


class AmountSplitter:

    @staticmethod
    @func_logging(level="DEBUG")
    def split_with_dirichlet(
        total_amount: float,
        min_amount: float,
        split_count: int
    ) -> List[float]:
        # Dirichlet 분포로 수량을 여러 조각으로 분할
        if split_count == 1:
            return [total_amount]

        alphas = np.ones(split_count)
        ratios = np.random.dirichlet(alphas)
        raw_pieces = ratios * total_amount

        rounded_pieces = [
            MathUtils.round_to_min_unit(piece, min_amount)
            for piece in raw_pieces
        ]

        remainder = total_amount - sum(rounded_pieces)
        rounded_pieces[-1] += remainder

        non_zero_pieces = [piece for piece in rounded_pieces if piece > 0]

        if not non_zero_pieces:
            return [total_amount]

        return non_zero_pieces
