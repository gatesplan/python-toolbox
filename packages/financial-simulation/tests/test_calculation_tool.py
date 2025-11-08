"""Tests for CalculationTool."""

import pytest
import numpy as np
import sys
from pathlib import Path

# 패키지 루트를 sys.path에 추가 (설치 없이 테스트)
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from financial_simulation.tradesim.calculation_tool import CalculationTool


class TestRoundToMinAmount:
    """round_to_min_amount 메서드 테스트."""

    def test_basic_rounding(self):
        """기본 내림 테스트."""
        assert CalculationTool.round_to_min_amount(1.234, 0.01) == 1.23
        assert CalculationTool.round_to_min_amount(10.567, 0.1) == 10.5
        assert CalculationTool.round_to_min_amount(5.0, 1.0) == 5.0

    def test_exact_multiples(self):
        """정확히 배수인 경우."""
        assert CalculationTool.round_to_min_amount(10.0, 0.5) == 10.0
        assert CalculationTool.round_to_min_amount(100.0, 25.0) == 100.0

    def test_zero_and_negative(self):
        """0과 음수 처리."""
        assert CalculationTool.round_to_min_amount(0, 0.01) == 0.0
        assert CalculationTool.round_to_min_amount(-1.5, 0.1) == 0.0
        assert CalculationTool.round_to_min_amount(-100, 10) == 0.0

    def test_very_small_amounts(self):
        """최소 단위보다 작은 금액."""
        assert CalculationTool.round_to_min_amount(0.001, 0.01) == 0.0
        assert CalculationTool.round_to_min_amount(0.05, 0.1) == 0.0


class TestGetPriceSample:
    """get_price_sample 메서드 테스트."""

    def test_within_range(self):
        """샘플링된 가격이 지정된 범위 내에 있는지 확인."""
        np.random.seed(42)

        for _ in range(100):
            price = CalculationTool.get_price_sample(100, 110, 105, 2)
            assert 100 <= price <= 110

    def test_tight_range_clipping(self):
        """좁은 범위에서 클리핑 확인."""
        np.random.seed(42)

        for _ in range(100):
            price = CalculationTool.get_price_sample(100, 102, 105, 5)
            assert 100 <= price <= 102

    def test_z_score_limits(self):
        """z-score 제한 확인."""
        np.random.seed(42)

        mean = 100
        std = 5
        min_z = -2.0
        max_z = 2.0

        for _ in range(100):
            price = CalculationTool.get_price_sample(0, 200, mean, std, min_z, max_z)
            # z-score 제한으로 mean ± 2*std 범위 내
            assert mean - 2 * std <= price <= mean + 2 * std

    def test_custom_z_score_range(self):
        """커스텀 z-score 범위."""
        np.random.seed(42)

        mean = 50
        std = 10

        for _ in range(100):
            price = CalculationTool.get_price_sample(0, 100, mean, std, -1.0, 1.0)
            # z-score 제한으로 mean ± 1*std 범위 내
            assert mean - 1 * std <= price <= mean + 1 * std


class TestGetSeparatedAmountSequence:
    """get_separated_amount_sequence 메서드 테스트."""

    def test_sum_preserved(self):
        """분할 후 합이 원래 금액과 동일한지 확인."""
        np.random.seed(42)

        base = 10.0
        pieces = CalculationTool.get_separated_amount_sequence(base, 0.1, 3)

        assert len(pieces) == 3
        assert abs(sum(pieces) - base) < 1e-10

    def test_single_piece(self):
        """단일 조각 반환."""
        result = CalculationTool.get_separated_amount_sequence(7.5, 0.1, 1)
        assert result == [7.5]

    def test_all_pieces_non_negative(self):
        """모든 조각이 0보다 큰지 확인 (0인 조각은 제거되어야 함)."""
        np.random.seed(42)

        pieces = CalculationTool.get_separated_amount_sequence(10.0, 0.1, 5)

        for piece in pieces:
            assert piece > 0

    def test_min_trade_amount_compliance(self):
        """모든 조각이 0보다 크고, 각 조각(마지막 제외)이 최소 거래 단위의 배수인지 확인."""
        np.random.seed(42)

        min_trade = 1.0
        pieces = CalculationTool.get_separated_amount_sequence(10.0, min_trade, 3)

        # 모든 조각이 0보다 커야 함
        assert all(piece > 0 for piece in pieces)

        # 마지막 조각은 잔여량이 포함될 수 있으므로 제외
        for piece in pieces[:-1]:
            remainder = piece % min_trade
            assert abs(remainder) < 1e-10 or abs(remainder - min_trade) < 1e-10

    def test_reproducibility(self):
        """동일한 시드로 재현 가능한지 확인."""
        np.random.seed(42)
        pieces1 = CalculationTool.get_separated_amount_sequence(10.0, 0.1, 3)

        np.random.seed(42)
        pieces2 = CalculationTool.get_separated_amount_sequence(10.0, 0.1, 3)

        assert pieces1 == pieces2

    def test_large_split(self):
        """많은 수로 분할."""
        np.random.seed(42)

        base = 100.0
        pieces = CalculationTool.get_separated_amount_sequence(base, 0.01, 10)

        assert len(pieces) == 10
        assert abs(sum(pieces) - base) < 1e-9


class TestGetPriceRange:
    """get_price_range 메서드 테스트."""

    def test_price_in_body(self):
        """가격이 body 범위에 있는 경우."""
        from financial_assets.price import Price

        # o=50500, c=49500 → bodybottom=49500, bodytop=50500
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        assert CalculationTool.get_price_range(price, 49500) == "body"
        assert CalculationTool.get_price_range(price, 50000) == "body"
        assert CalculationTool.get_price_range(price, 50500) == "body"

    def test_price_in_head(self):
        """가격이 head 범위에 있는 경우."""
        from financial_assets.price import Price

        # o=50500, c=49500, h=51000 → bodytop=50500, head: 50500 < x <= 51000
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        assert CalculationTool.get_price_range(price, 50600) == "head"
        assert CalculationTool.get_price_range(price, 50800) == "head"
        assert CalculationTool.get_price_range(price, 51000) == "head"

    def test_price_in_tail(self):
        """가격이 tail 범위에 있는 경우."""
        from financial_assets.price import Price

        # o=50500, c=49500, l=49000 → bodybottom=49500, tail: 49000 <= x < 49500
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        assert CalculationTool.get_price_range(price, 49000) == "tail"
        assert CalculationTool.get_price_range(price, 49200) == "tail"
        assert CalculationTool.get_price_range(price, 49499) == "tail"

    def test_price_outside_range(self):
        """가격이 캔들 범위 밖에 있는 경우."""
        from financial_assets.price import Price

        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        assert CalculationTool.get_price_range(price, 48999) == "none"
        assert CalculationTool.get_price_range(price, 51001) == "none"

    def test_bullish_candle(self):
        """양봉(close > open)인 경우."""
        from financial_assets.price import Price

        # o=49500, c=50500 → bodybottom=49500, bodytop=50500
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 49500, 50500, 100)

        assert CalculationTool.get_price_range(price, 49500) == "body"
        assert CalculationTool.get_price_range(price, 50500) == "body"
        assert CalculationTool.get_price_range(price, 50600) == "head"
        assert CalculationTool.get_price_range(price, 49000) == "tail"
