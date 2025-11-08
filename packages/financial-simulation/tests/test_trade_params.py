"""Tests for TradeParams."""

import pytest
import sys
from pathlib import Path

# 패키지 루트를 sys.path에 추가 (설치 없이 테스트)
package_root = Path(__file__).parent.parent
sys.path.insert(0, str(package_root))

from financial_simulation.tradesim.trade_params import TradeParams


class TestTradeParamsCreation:
    """TradeParams 생성 테스트."""

    def test_basic_creation(self):
        """기본 생성."""
        params = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )

        assert params.fill_amount == 1.5
        assert params.fill_price == 50000.0
        assert params.fill_index == 1

    def test_with_zero_values(self):
        """0 값으로 생성."""
        params = TradeParams(
            fill_amount=0.0,
            fill_price=0.0,
            fill_index=0
        )

        assert params.fill_amount == 0.0
        assert params.fill_price == 0.0
        assert params.fill_index == 0

    def test_with_large_values(self):
        """큰 값으로 생성."""
        params = TradeParams(
            fill_amount=999999.999,
            fill_price=123456.789,
            fill_index=100
        )

        assert params.fill_amount == 999999.999
        assert params.fill_price == 123456.789
        assert params.fill_index == 100


class TestTradeParamsImmutability:
    """TradeParams 불변성 테스트."""

    def test_frozen_dataclass(self):
        """frozen=True로 인한 불변성 확인."""
        params = TradeParams(
            fill_amount=1.0,
            fill_price=50000.0,
            fill_index=1
        )

        with pytest.raises(AttributeError):
            params.fill_amount = 2.0

        with pytest.raises(AttributeError):
            params.fill_price = 60000.0

        with pytest.raises(AttributeError):
            params.fill_index = 2


class TestTradeParamsEquality:
    """TradeParams 동등성 테스트."""

    def test_equality_same_values(self):
        """같은 값을 가진 인스턴스는 동등."""
        params1 = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )
        params2 = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )

        assert params1 == params2

    def test_inequality_different_values(self):
        """다른 값을 가진 인스턴스는 동등하지 않음."""
        params1 = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )
        params2 = TradeParams(
            fill_amount=2.0,
            fill_price=50000.0,
            fill_index=1
        )

        assert params1 != params2


class TestTradeParamsHash:
    """TradeParams 해시 가능성 테스트."""

    def test_hashable(self):
        """frozen dataclass는 해시 가능."""
        params1 = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )
        params2 = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )

        # set에 추가 가능
        params_set = {params1, params2}
        assert len(params_set) == 1  # 동등한 객체는 하나만 저장됨

    def test_use_as_dict_key(self):
        """딕셔너리 키로 사용 가능."""
        params = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )

        data = {params: "trade_data"}
        assert data[params] == "trade_data"


class TestTradeParamsRepresentation:
    """TradeParams 문자열 표현 테스트."""

    def test_repr(self):
        """repr 출력 확인."""
        params = TradeParams(
            fill_amount=1.5,
            fill_price=50000.0,
            fill_index=1
        )

        repr_str = repr(params)
        assert "TradeParams" in repr_str
        assert "fill_amount=1.5" in repr_str
        assert "fill_price=50000.0" in repr_str
        assert "fill_index=1" in repr_str
