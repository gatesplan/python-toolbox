"""
Tests for PairStack class
"""
import pytest
from financial_assets.token import Token
from financial_assets.pair import Pair, PairStack


class TestPairStackInit:
    """PairStack 초기화 테스트"""

    def test_empty_init(self):
        """빈 스택 생성"""
        stack = PairStack()
        assert stack.is_empty()
        assert len(stack) == 0

    def test_init_with_pairs(self):
        """초기 Pair들과 함께 생성"""
        pairs = [
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 25000.0)),
        ]
        stack = PairStack(pairs)
        assert len(stack) == 1  # 평단가 같아서 병합됨
        assert stack.total_asset_amount() == 1.5
        assert stack.total_value_amount() == 75000.0


class TestPairStackAppend:
    """PairStack append 테스트"""

    def test_append_to_empty_stack(self):
        """빈 스택에 Pair 추가"""
        stack = PairStack()
        pair = Pair(Token("BTC", 1.0), Token("USD", 50000.0))
        stack.append(pair)
        assert len(stack) == 1
        assert stack.total_asset_amount() == 1.0

    def test_append_with_same_mean_value_merges(self):
        """같은 평단가 Pair는 병합"""
        stack = PairStack()
        stack.append(Pair(Token("BTC", 1.0), Token("USD", 50000.0)))
        stack.append(Pair(Token("BTC", 0.5), Token("USD", 25000.0)))
        assert len(stack) == 1  # 병합됨
        assert stack.total_asset_amount() == 1.5
        assert stack.total_value_amount() == 75000.0

    def test_append_with_different_mean_value_separates(self):
        """다른 평단가 Pair는 분리"""
        stack = PairStack()
        stack.append(Pair(Token("BTC", 1.0), Token("USD", 50000.0)))
        stack.append(Pair(Token("BTC", 0.5), Token("USD", 26000.0)))  # 4% 차이
        assert len(stack) == 2  # 분리됨

    def test_append_with_threshold_boundary(self):
        """0.01% 경계 테스트"""
        stack = PairStack()
        stack.append(Pair(Token("BTC", 1.0), Token("USD", 50000.0)))

        # 0.01% 이내: 병합
        stack.append(Pair(Token("BTC", 1.0), Token("USD", 50004.0)))  # 0.008% 차이
        assert len(stack) == 1

        # 0.01% 초과: 분리
        stack.append(Pair(Token("BTC", 1.0), Token("USD", 50010.0)))  # 0.02% 차이
        assert len(stack) == 2

    def test_append_different_asset_symbol_returns_false(self):
        """다른 asset symbol Pair 추가 시 False 반환"""
        stack = PairStack()
        result1 = stack.append(Pair(Token("BTC", 1.0), Token("USD", 50000.0)))
        assert result1 is True
        result2 = stack.append(Pair(Token("ETH", 1.0), Token("USD", 2000.0)))
        assert result2 is False
        assert len(stack) == 1  # 추가되지 않음

    def test_append_different_value_symbol_returns_false(self):
        """다른 value symbol Pair 추가 시 False 반환"""
        stack = PairStack()
        result1 = stack.append(Pair(Token("BTC", 1.0), Token("USD", 50000.0)))
        assert result1 is True
        result2 = stack.append(Pair(Token("BTC", 1.0), Token("KRW", 60000000.0)))
        assert result2 is False
        assert len(stack) == 1  # 추가되지 않음


class TestPairStackMeanValue:
    """PairStack mean_value 테스트"""

    def test_mean_value_single_layer(self):
        """단일 레이어 평단가"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        assert stack.mean_value() == 50000.0

    def test_mean_value_multiple_layers(self):
        """여러 레이어 평단가"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
        ])
        # (50000 + 26000) / (1.0 + 0.5) = 50666.67
        assert abs(stack.mean_value() - 50666.67) < 0.01

    def test_mean_value_empty_stack_raises(self):
        """빈 스택 평단가 에러"""
        stack = PairStack()
        with pytest.raises(ValueError, match="stack is empty"):
            stack.mean_value()


class TestPairStackTotals:
    """PairStack total_asset_amount, total_value_amount 테스트"""

    def test_total_amounts(self):
        """전체 수량 합계"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
        ])
        assert stack.total_asset_amount() == 1.5
        assert stack.total_value_amount() == 76000.0

    def test_total_amounts_empty_stack(self):
        """빈 스택 전체 수량"""
        stack = PairStack()
        assert stack.total_asset_amount() == 0.0
        assert stack.total_value_amount() == 0.0


class TestPairStackFlatten:
    """PairStack flatten 테스트"""

    def test_flatten_single_layer(self):
        """단일 레이어 병합"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        flat = stack.flatten()
        assert flat.get_asset() == 1.0
        assert flat.get_value() == 50000.0

    def test_flatten_multiple_layers(self):
        """여러 레이어 병합"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
        ])
        flat = stack.flatten()
        assert flat.get_asset() == 1.5
        assert flat.get_value() == 76000.0

    def test_flatten_empty_stack_raises(self):
        """빈 스택 병합 에러"""
        stack = PairStack()
        with pytest.raises(ValueError, match="stack is empty"):
            stack.flatten()


class TestPairStackSplitByAssetAmount:
    """PairStack split_by_asset_amount 테스트"""

    def test_split_entire_stack(self):
        """전체 분리"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
        ])
        splitted = stack.split_by_asset_amount(1.5)

        # 원본은 비어야 함
        assert stack.is_empty()

        # 분리된 것은 전체
        assert len(splitted) == 2
        assert splitted.total_asset_amount() == 1.5

    def test_split_partial_single_layer(self):
        """단일 레이어 부분 분리"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        splitted = stack.split_by_asset_amount(0.3)

        # 원본: 0.7 BTC
        assert stack.total_asset_amount() == 0.7
        assert stack.total_value_amount() == 35000.0

        # 분리: 0.3 BTC
        assert splitted.total_asset_amount() == 0.3
        assert splitted.total_value_amount() == 15000.0

    def test_split_across_multiple_layers(self):
        """여러 레이어 걸쳐 분리 (비율 기반)"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.8), Token("USD", 42000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 27000.0)),
        ])
        # 총 2.3 BTC에서 1.5 BTC 분리 (비율: 1.5/2.3 ≈ 0.652)
        splitted = stack.split_by_asset_amount(1.5)

        # 분리: 1.5 BTC
        assert abs(splitted.total_asset_amount() - 1.5) < 0.01

        # 원본: 0.8 BTC 남음
        assert abs(stack.total_asset_amount() - 0.8) < 0.01

    def test_split_negative_amount_raises(self):
        """음수 분리 에러"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        with pytest.raises(ValueError, match="non-negative"):
            stack.split_by_asset_amount(-0.5)

    def test_split_exceeds_total_raises(self):
        """총량 초과 분리 에러"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        with pytest.raises(ValueError, match="exceeds total"):
            stack.split_by_asset_amount(2.0)


class TestPairStackSplitByValueAmount:
    """PairStack split_by_value_amount 테스트"""

    def test_split_by_value(self):
        """value 기준 분리"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        splitted = stack.split_by_value_amount(15000.0)

        # 원본: 35000 USD
        assert stack.total_value_amount() == 35000.0
        assert abs(stack.total_asset_amount() - 0.7) < 0.0001

        # 분리: 15000 USD
        assert splitted.total_value_amount() == 15000.0
        assert abs(splitted.total_asset_amount() - 0.3) < 0.0001

    def test_split_by_value_across_layers(self):
        """여러 레이어 걸쳐 value 기준 분리"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 26000.0)),
        ])
        splitted = stack.split_by_value_amount(60000.0)

        # 원본: 16000 USD
        assert abs(stack.total_value_amount() - 16000.0) < 0.01

        # 분리: 60000 USD
        assert abs(splitted.total_value_amount() - 60000.0) < 0.01


class TestPairStackSplitByRatio:
    """PairStack split_by_ratio 테스트"""

    def test_split_by_ratio_half(self):
        """50% 분리 (value 기준, 스택 위부터)"""
        stack = PairStack([
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.8), Token("USD", 42000.0)),
        ])
        # 총 value: 92000, 50% = 46000
        # 스택 위(마지막): 42000 전체 + 첫번째에서 4000
        splitted = stack.split_by_ratio(0.5)

        # 분리: 46000 USD (총 value의 50%)
        assert abs(splitted.total_value_amount() - 46000.0) < 0.01

        # 원본: 46000 USD 남음
        assert abs(stack.total_value_amount() - 46000.0) < 0.01

    def test_split_by_ratio_zero(self):
        """0% 분리 (아무것도 안 함)"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        splitted = stack.split_by_ratio(0.0)

        assert stack.total_asset_amount() == 1.0
        assert splitted.is_empty()

    def test_split_by_ratio_one(self):
        """100% 분리 (전체 이동)"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        splitted = stack.split_by_ratio(1.0)

        assert stack.is_empty()
        assert splitted.total_asset_amount() == 1.0

    def test_split_by_ratio_invalid_raises(self):
        """잘못된 비율 에러"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])
        with pytest.raises(ValueError, match="between 0 and 1"):
            stack.split_by_ratio(1.5)
        with pytest.raises(ValueError, match="between 0 and 1"):
            stack.split_by_ratio(-0.1)


class TestPairStackEdgeCases:
    """PairStack 엣지 케이스 테스트"""

    def test_append_zero_asset_amount(self):
        """asset amount가 0인 Pair 추가"""
        stack = PairStack()
        stack.append(Pair(Token("BTC", 1.0), Token("USD", 50000.0)))
        stack.append(Pair(Token("BTC", 0.0), Token("USD", 0.0)))
        assert len(stack) == 2  # 병합 불가, 분리 유지

    def test_merge_preserves_order(self):
        """병합 시 순서 유지 확인"""
        pairs = [
            Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
            Pair(Token("BTC", 0.5), Token("USD", 25000.0)),  # 병합됨
            Pair(Token("BTC", 0.3), Token("USD", 15600.0)),  # 분리 (4% 차이)
        ]
        stack = PairStack(pairs)
        assert len(stack) == 2
        # 첫 번째 레이어는 병합된 것
        flat = stack.flatten()
        assert abs(flat.get_asset() - 1.8) < 0.0001

    def test_string_representations(self):
        """문자열 표현 테스트"""
        stack = PairStack([Pair(Token("BTC", 1.0), Token("USD", 50000.0))])

        # __repr__
        repr_str = repr(stack)
        assert "PairStack" in repr_str

        # __str__
        str_str = str(stack)
        assert "PairStack" in str_str
        assert "1 layers" in str_str or "layer" in str_str

        # 빈 스택
        empty = PairStack()
        assert "empty" in str(empty)
