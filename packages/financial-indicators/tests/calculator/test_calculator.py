import numpy as np
import pandas as pd
import pytest
from financial_indicators.calculator.calculator import IndicatorCalculator
from financial_indicators.registry import registry


def create_test_candle_df(length=100):
    return pd.DataFrame({
        'timestamp': np.arange(1609459200, 1609459200 + length * 86400, 86400),
        'open': np.array([100.0 + i for i in range(length)]),
        'high': np.array([105.0 + i for i in range(length)]),
        'low': np.array([95.0 + i for i in range(length)]),
        'close': np.array([102.0 + i for i in range(length)]),
        'volume': np.array([1000.0 + i * 10 for i in range(length)])
    })


class TestIndicatorCalculator:
    def test_initialization(self):
        calc = IndicatorCalculator(registry)
        assert calc._registry is registry
        assert calc._cache == {}

    def test_calculate_single_indicator(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        result = calc.calculate("sma", df, period=20)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(df)

    def test_calculate_with_different_params(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        sma_20 = calc.calculate("sma", df, period=20)
        sma_50 = calc.calculate("sma", df, period=50)

        assert not np.array_equal(sma_20, sma_50)

    def test_caching_same_request(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        result1 = calc.calculate("sma", df, period=20)
        result2 = calc.calculate("sma", df, period=20)

        assert np.array_equal(result1, result2)
        assert calc.get_cache_size() == 1

    def test_caching_different_dataframes(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df1 = create_test_candle_df(50)
        df2 = create_test_candle_df(50)

        result1 = calc.calculate("sma", df1, period=20)
        result2 = calc.calculate("sma", df2, period=20)

        assert calc.get_cache_size() == 2

    def test_calculate_rsi(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        result = calc.calculate("rsi", df, period=14)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(df)
        assert np.all((result >= 0) & (result <= 100))

    def test_calculate_rsi_entropy_returns_dict(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)

        np.random.seed(42)
        df = pd.DataFrame({
            'close': 100.0 + np.cumsum(np.random.randn(400) * 0.5)
        })

        result = calc.calculate("rsi_entropy", df, rsi_period=20, entropy_window=365)

        assert isinstance(result, dict)
        assert "base" in result
        assert "z-1" in result
        assert "z+1" in result
        assert "buy" in result
        assert "sell" in result

    def test_calculate_batch(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        results = calc.calculate_batch([
            {"name": "sma", "period": 20},
            {"name": "sma", "period": 50},
            {"name": "ema", "period": 12}
        ], df)

        assert "sma_20" in results
        assert "sma_50" in results
        assert "ema_12" in results
        assert isinstance(results["sma_20"], np.ndarray)

    def test_calculate_batch_clears_cache_by_default(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        # 캐시에 데이터 추가
        calc.calculate("sma", df, period=10)
        assert calc.get_cache_size() == 1

        # batch 호출 시 캐시 클리어 (기본 동작)
        calc.calculate_batch([{"name": "ema", "period": 12}], df)

        # batch에서 계산한 것만 캐시에 있어야 함
        assert calc.get_cache_size() == 1

    def test_calculate_batch_preserves_cache_when_disabled(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        # 캐시에 데이터 추가
        calc.calculate("sma", df, period=10)
        assert calc.get_cache_size() == 1

        # batch 호출 시 캐시 유지
        calc.calculate_batch([{"name": "ema", "period": 12}], df, clear_cache=False)

        # 기존 캐시 + 새 계산 = 2개
        assert calc.get_cache_size() == 2

    def test_calculate_batch_with_rsi_entropy(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)

        np.random.seed(42)
        df = pd.DataFrame({
            'close': 100.0 + np.cumsum(np.random.randn(400) * 0.5)
        })

        results = calc.calculate_batch([
            {"name": "sma", "period": 20},
            {"name": "rsi_entropy", "rsi_period": 20, "entropy_window": 365}
        ], df)

        assert "sma_20" in results
        assert "rsi_entropy_20_365" in results
        assert isinstance(results["rsi_entropy_20_365"], dict)

    def test_clear_cache(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        calc.calculate("sma", df, period=20)
        calc.calculate("ema", df, period=12)

        assert calc.get_cache_size() == 2

        calc.clear_cache()

        assert calc.get_cache_size() == 0

    def test_get_cache_size(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        assert calc.get_cache_size() == 0

        calc.calculate("sma", df, period=20)
        assert calc.get_cache_size() == 1

        calc.calculate("ema", df, period=12)
        assert calc.get_cache_size() == 2

    def test_cache_key_generation_with_sorted_params(self):
        import financial_indicators.indicators

        calc = IndicatorCalculator(registry)
        df = create_test_candle_df(50)

        calc.calculate("rsi", df, period=14, use="close")
        calc.calculate("rsi", df, use="close", period=14)

        assert calc.get_cache_size() == 1
