"""Tests for Symbol class"""

import pytest
from financial_assets.symbol import Symbol


class TestSymbolParsing:
    """Symbol 파싱 테스트"""

    def test_parse_slash_format(self):
        """슬래시 형식 파싱"""
        symbol = Symbol("BTC/USDT")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"

    def test_parse_dash_format(self):
        """하이픈 형식 파싱"""
        symbol = Symbol("BTC-USDT")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"

    def test_parse_lowercase_to_uppercase(self):
        """소문자 입력을 대문자로 변환"""
        symbol = Symbol("btc/usdt")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"

    def test_parse_mixed_case(self):
        """대소문자 혼합 입력"""
        symbol = Symbol("BtC-UsDt")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"

    def test_parse_with_whitespace(self):
        """공백 포함 입력 처리"""
        symbol = Symbol(" BTC / USDT ")
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"

    def test_parse_longer_symbols(self):
        """긴 심볼 파싱 (MATIC, DOGE 등)"""
        symbol = Symbol("MATIC/USDT")
        assert symbol.base == "MATIC"
        assert symbol.quote == "USDT"

    def test_parse_fails_without_separator(self):
        """구분자 없는 형식은 파싱 실패"""
        with pytest.raises(ValueError, match="Invalid symbol format"):
            Symbol("BTCUSDT")

    def test_parse_fails_with_multiple_separators(self):
        """여러 구분자가 있으면 파싱 실패"""
        with pytest.raises(ValueError, match="Expected exactly 2 parts"):
            Symbol("BTC/USDT/ETH")

    def test_parse_fails_with_empty_base(self):
        """base가 비어있으면 파싱 실패"""
        with pytest.raises(ValueError, match="cannot be empty"):
            Symbol("/USDT")

    def test_parse_fails_with_empty_quote(self):
        """quote가 비어있으면 파싱 실패"""
        with pytest.raises(ValueError, match="cannot be empty"):
            Symbol("BTC/")


class TestSymbolOutput:
    """Symbol 출력 형식 테스트"""

    def test_to_slash(self):
        """슬래시 형식 출력"""
        symbol = Symbol("BTC/USDT")
        assert symbol.to_slash() == "BTC/USDT"

    def test_to_dash(self):
        """하이픈 형식 출력"""
        symbol = Symbol("BTC/USDT")
        assert symbol.to_dash() == "BTC-USDT"

    def test_to_compact(self):
        """compact 형식 출력"""
        symbol = Symbol("BTC/USDT")
        assert symbol.to_compact() == "BTCUSDT"

    def test_to_slash_from_dash_input(self):
        """하이픈 입력 → 슬래시 출력"""
        symbol = Symbol("BTC-USDT")
        assert symbol.to_slash() == "BTC/USDT"

    def test_to_dash_from_slash_input(self):
        """슬래시 입력 → 하이픈 출력"""
        symbol = Symbol("BTC/USDT")
        assert symbol.to_dash() == "BTC-USDT"

    def test_all_formats_consistent(self):
        """모든 출력 형식이 일관성 있음"""
        symbol = Symbol("matic-usdt")
        assert symbol.to_slash() == "MATIC/USDT"
        assert symbol.to_dash() == "MATIC-USDT"
        assert symbol.to_compact() == "MATICUSDT"


class TestSymbolEquality:
    """Symbol 동등성 비교 테스트"""

    def test_equality_same_format(self):
        """같은 형식으로 생성된 Symbol 비교"""
        symbol1 = Symbol("BTC/USDT")
        symbol2 = Symbol("BTC/USDT")
        assert symbol1 == symbol2

    def test_equality_different_format(self):
        """다른 형식으로 생성되었지만 같은 Symbol"""
        symbol1 = Symbol("BTC/USDT")
        symbol2 = Symbol("BTC-USDT")
        assert symbol1 == symbol2

    def test_equality_case_insensitive(self):
        """대소문자 무관하게 동등성 비교"""
        symbol1 = Symbol("btc/usdt")
        symbol2 = Symbol("BTC-USDT")
        assert symbol1 == symbol2

    def test_inequality_different_base(self):
        """base가 다르면 다름"""
        symbol1 = Symbol("BTC/USDT")
        symbol2 = Symbol("ETH/USDT")
        assert symbol1 != symbol2

    def test_inequality_different_quote(self):
        """quote가 다르면 다름"""
        symbol1 = Symbol("BTC/USDT")
        symbol2 = Symbol("BTC/BUSD")
        assert symbol1 != symbol2

    def test_inequality_with_non_symbol(self):
        """Symbol이 아닌 객체와 비교"""
        symbol = Symbol("BTC/USDT")
        assert symbol != "BTC/USDT"
        assert symbol != 123


class TestSymbolHash:
    """Symbol 해시 테스트 (dict 키로 사용)"""

    def test_hashable(self):
        """Symbol을 dict 키로 사용 가능"""
        symbol = Symbol("BTC/USDT")
        data = {symbol: 50000.0}
        assert data[symbol] == 50000.0

    def test_same_symbol_same_hash(self):
        """같은 Symbol은 같은 해시"""
        symbol1 = Symbol("BTC/USDT")
        symbol2 = Symbol("BTC-USDT")
        assert hash(symbol1) == hash(symbol2)

    def test_different_symbol_different_hash(self):
        """다른 Symbol은 다른 해시 (일반적으로)"""
        symbol1 = Symbol("BTC/USDT")
        symbol2 = Symbol("ETH/USDT")
        # 해시 충돌은 가능하지만 일반적으로 달라야 함
        assert hash(symbol1) != hash(symbol2)

    def test_dict_key_replacement(self):
        """dict에서 같은 Symbol은 같은 키로 취급"""
        data = {}
        data[Symbol("BTC/USDT")] = 50000.0
        data[Symbol("BTC-USDT")] = 51000.0  # 같은 키, 값 덮어쓰기
        assert len(data) == 1
        assert data[Symbol("BTC/USDT")] == 51000.0


class TestSymbolStringRepresentation:
    """Symbol 문자열 표현 테스트"""

    def test_str_returns_slash_format(self):
        """str()은 슬래시 형식 반환"""
        symbol = Symbol("BTC-USDT")
        assert str(symbol) == "BTC/USDT"

    def test_repr_shows_base_and_quote(self):
        """repr()은 base, quote를 명시적으로 보여줌"""
        symbol = Symbol("BTC/USDT")
        repr_str = repr(symbol)
        assert "base='BTC'" in repr_str
        assert "quote='USDT'" in repr_str
        assert "Symbol" in repr_str


class TestSymbolProperties:
    """Symbol 속성 접근 테스트"""

    def test_base_property(self):
        """base 속성 읽기"""
        symbol = Symbol("ETH/BTC")
        assert symbol.base == "ETH"

    def test_quote_property(self):
        """quote 속성 읽기"""
        symbol = Symbol("ETH/BTC")
        assert symbol.quote == "BTC"

    def test_properties_are_readonly(self):
        """base, quote는 읽기 전용 (수정 불가)"""
        symbol = Symbol("BTC/USDT")
        with pytest.raises(AttributeError):
            symbol.base = "ETH"  # type: ignore
        with pytest.raises(AttributeError):
            symbol.quote = "BUSD"  # type: ignore


class TestSymbolEdgeCases:
    """Symbol 엣지 케이스 테스트"""

    def test_single_character_symbols(self):
        """1글자 심볼"""
        symbol = Symbol("A/B")
        assert symbol.base == "A"
        assert symbol.quote == "B"
        assert symbol.to_compact() == "AB"

    def test_very_long_symbols(self):
        """긴 심볼"""
        symbol = Symbol("VERYLONGTOKEN/ANOTHERVERYLONGTOKEN")
        assert symbol.base == "VERYLONGTOKEN"
        assert symbol.quote == "ANOTHERVERYLONGTOKEN"

    def test_numeric_symbols(self):
        """숫자가 포함된 심볼 (실제로는 드물지만)"""
        symbol = Symbol("TOKEN123/USDT")
        assert symbol.base == "TOKEN123"
        assert symbol.quote == "USDT"
