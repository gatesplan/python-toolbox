import pytest
from financial_indicators.registry.registry import IndicatorRegistry, IndicatorNotFoundError


class TestIndicatorRegistry:
    def test_register_and_get(self):
        registry = IndicatorRegistry()

        @registry.register("test_indicator")
        def test_func(x):
            return x * 2

        func = registry.get("test_indicator")
        assert func(5) == 10

    def test_register_returns_original_function(self):
        registry = IndicatorRegistry()

        def original_func(x):
            return x + 1

        decorated = registry.register("test")(original_func)
        assert decorated is original_func

    def test_get_nonexistent_raises_error(self):
        registry = IndicatorRegistry()

        with pytest.raises(IndicatorNotFoundError, match="'unknown'"):
            registry.get("unknown")

    def test_has_returns_true_for_registered(self):
        registry = IndicatorRegistry()

        @registry.register("exists")
        def func():
            pass

        assert registry.has("exists") is True

    def test_has_returns_false_for_nonexistent(self):
        registry = IndicatorRegistry()
        assert registry.has("nonexistent") is False

    def test_list_all_returns_sorted_names(self):
        registry = IndicatorRegistry()

        @registry.register("zulu")
        def func1():
            pass

        @registry.register("alpha")
        def func2():
            pass

        @registry.register("bravo")
        def func3():
            pass

        names = registry.list_all()
        assert names == ["alpha", "bravo", "zulu"]

    def test_list_all_empty_registry(self):
        registry = IndicatorRegistry()
        assert registry.list_all() == []

    def test_duplicate_registration_overwrites(self):
        registry = IndicatorRegistry()

        @registry.register("duplicate")
        def func1(x):
            return x * 2

        @registry.register("duplicate")
        def func2(x):
            return x * 3

        func = registry.get("duplicate")
        assert func(5) == 15

    def test_multiple_indicators(self):
        registry = IndicatorRegistry()

        @registry.register("sma")
        def sma(period):
            return f"SMA-{period}"

        @registry.register("ema")
        def ema(period):
            return f"EMA-{period}"

        @registry.register("rsi")
        def rsi(period):
            return f"RSI-{period}"

        assert registry.get("sma")(20) == "SMA-20"
        assert registry.get("ema")(12) == "EMA-12"
        assert registry.get("rsi")(14) == "RSI-14"
        assert len(registry.list_all()) == 3
