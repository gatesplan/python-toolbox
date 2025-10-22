"""Tests for CalculationTool."""

import pytest
import numpy as np
from financial_simulation.tradesim import CalculationTool


class TestRoundToMinAmount:
    """Tests for round_to_min_amount method."""

    def test_round_to_min_amount_basic(self):
        """기본적인 반올림 테스트."""
        calc = CalculationTool()

        assert calc.round_to_min_amount(1.234, 0.01) == 1.23
        assert calc.round_to_min_amount(10.567, 0.1) == 10.5
        assert calc.round_to_min_amount(5.0, 1.0) == 5.0

    def test_round_to_min_amount_edge_cases(self):
        """엣지 케이스 테스트."""
        calc = CalculationTool()

        assert calc.round_to_min_amount(0, 0.01) == 0.0
        assert calc.round_to_min_amount(0.001, 0.01) == 0.0

    def test_round_to_min_amount_negative(self):
        """음수 처리 테스트."""
        calc = CalculationTool()

        assert calc.round_to_min_amount(-1.5, 0.1) == 0.0


class TestGetPriceSample:
    """Tests for get_price_sample method."""

    def test_price_sample_within_range(self):
        """샘플링된 가격이 범위 내에 있는지 테스트."""
        calc = CalculationTool()
        np.random.seed(42)

        for _ in range(100):
            price = calc.get_price_sample(100, 110, 105, 2)
            assert 100 <= price <= 110

    def test_price_sample_clipping(self):
        """범위를 벗어나는 경우 클리핑 테스트."""
        calc = CalculationTool()
        np.random.seed(42)

        for _ in range(100):
            price = calc.get_price_sample(100, 102, 105, 5)
            assert 100 <= price <= 102

    def test_price_sample_z_score_limit(self):
        """z-score 제한 테스트."""
        calc = CalculationTool()
        np.random.seed(42)

        mean = 100
        std = 5
        min_z = -2.0
        max_z = 2.0

        for _ in range(100):
            price = calc.get_price_sample(0, 200, mean, std, min_z, max_z)
            # z-score 제한으로 인해 mean ± 2*std 범위 내여야 함
            assert mean - 2 * std <= price <= mean + 2 * std


class TestGetSeparatedAmountSequence:
    """Tests for get_separated_amount_sequence method."""

    def test_separate_amount_sum_preserved(self):
        """분할 후 합이 보존되는지 테스트."""
        calc = CalculationTool()
        np.random.seed(42)

        pieces = calc.get_separated_amount_sequence(10.0, 0.1, 3)

        assert len(pieces) == 3
        assert abs(sum(pieces) - 10.0) < 1e-10  # 부동소수점 오차 허용

    def test_separate_amount_min_trade_amount(self):
        """각 조각이 최소 거래 단위의 배수인지 테스트."""
        calc = CalculationTool()
        np.random.seed(42)

        min_trade = 1.0
        pieces = calc.get_separated_amount_sequence(5.0, min_trade, 2)

        for piece in pieces[:-1]:  # 마지막 조각 제외 (잔여량 포함 가능)
            if piece > 0:
                remainder = piece % min_trade
                assert abs(remainder) < 1e-10 or abs(remainder - min_trade) < 1e-10

    def test_separate_amount_single_piece(self):
        """단일 조각 테스트."""
        calc = CalculationTool()

        pieces = calc.get_separated_amount_sequence(7.5, 0.1, 1)

        assert pieces == [7.5]

    def test_separate_amount_remainder_handling(self):
        """잔여량이 마지막 조각에 추가되는지 테스트."""
        calc = CalculationTool()
        np.random.seed(42)

        pieces = calc.get_separated_amount_sequence(10.0, 0.3, 3)

        # 합은 정확히 10.0이어야 함
        assert abs(sum(pieces) - 10.0) < 1e-10

    def test_separate_amount_reproducibility(self):
        """랜덤 시드 고정 시 재현 가능한지 테스트."""
        calc = CalculationTool()

        np.random.seed(42)
        pieces1 = calc.get_separated_amount_sequence(10.0, 0.1, 3)

        np.random.seed(42)
        pieces2 = calc.get_separated_amount_sequence(10.0, 0.1, 3)

        assert pieces1 == pieces2


class TestGetPriceRange:
    """Tests for get_price_range method."""

    def test_price_in_body_range(self):
        """가격이 body 범위에 있을 때."""
        from financial_assets.price import Price

        calc = CalculationTool()
        # o=50500, c=49500 → bodybottom=49500, bodytop=50500
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        # Body 범위 내 가격들
        assert calc.get_price_range(price, 49500) == "body"
        assert calc.get_price_range(price, 50000) == "body"
        assert calc.get_price_range(price, 50500) == "body"

    def test_price_in_head_range(self):
        """가격이 head 범위에 있을 때."""
        from financial_assets.price import Price

        calc = CalculationTool()
        # o=50500, c=49500, h=51000 → bodytop=50500, head: 50500 ~ 51000
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        # Head 범위 (bodytop < x <= h)
        assert calc.get_price_range(price, 50600) == "head"
        assert calc.get_price_range(price, 50800) == "head"
        assert calc.get_price_range(price, 51000) == "head"

    def test_price_in_tail_range(self):
        """가격이 tail 범위에 있을 때."""
        from financial_assets.price import Price

        calc = CalculationTool()
        # o=50500, c=49500, l=49000 → bodybottom=49500, tail: 49000 ~ 49500
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        # Tail 범위 (l <= x < bodybottom)
        assert calc.get_price_range(price, 49000) == "tail"
        assert calc.get_price_range(price, 49200) == "tail"
        assert calc.get_price_range(price, 49499) == "tail"

    def test_price_outside_range(self):
        """가격이 캔들 범위 밖에 있을 때."""
        from financial_assets.price import Price

        calc = CalculationTool()
        price = Price("binance", "BTC/USD", 1234567890, 51000, 49000, 50500, 49500, 100)

        # 범위 밖
        assert calc.get_price_range(price, 48999) == "none"  # low보다 낮음
        assert calc.get_price_range(price, 51001) == "none"  # high보다 높음


class TestCalculationToolStateless:
    """Tests for stateless behavior."""

    def test_methods_have_no_side_effects(self):
        """메서드 호출이 인스턴스 상태를 변경하지 않는지 테스트."""
        calc = CalculationTool()

        # 초기 상태 확인
        initial_dict = calc.__dict__.copy()

        # 메서드 호출
        calc.round_to_min_amount(1.234, 0.01)
        calc.get_price_sample(100, 110, 105, 2)
        calc.get_separated_amount_sequence(10.0, 0.1, 3)

        # 상태가 변경되지 않았는지 확인
        assert calc.__dict__ == initial_dict
