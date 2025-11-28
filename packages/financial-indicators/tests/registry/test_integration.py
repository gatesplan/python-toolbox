import numpy as np
import pandas as pd
from financial_indicators.registry import registry


class TestRegistryIntegration:
    def test_indicators_auto_registered(self):
        import financial_indicators.indicators

        registered = registry.list_all()
        assert "sma" in registered
        assert "ema" in registered
        assert "rsi" in registered
        assert "rsi_entropy" in registered

    def test_get_and_execute_sma(self):
        import financial_indicators.indicators

        sma_func = registry.get("sma")

        df = pd.DataFrame({
            'close': [100.0, 101.0, 102.0, 103.0, 104.0]
        })

        result = sma_func(df, period=3)
        assert len(result) == len(df)
        assert isinstance(result, np.ndarray)

    def test_get_and_execute_rsi(self):
        import financial_indicators.indicators

        rsi_func = registry.get("rsi")

        df = pd.DataFrame({
            'close': np.array([100.0 + i for i in range(20)])
        })

        result = rsi_func(df, period=14)
        assert len(result) == len(df)
        assert isinstance(result, np.ndarray)

    def test_get_and_execute_rsi_entropy(self):
        import financial_indicators.indicators

        rsi_entropy_func = registry.get("rsi_entropy")

        np.random.seed(42)
        df = pd.DataFrame({
            'close': 100.0 + np.cumsum(np.random.randn(400) * 0.5)
        })

        result = rsi_entropy_func(df)
        assert isinstance(result, dict)
        assert "base" in result
        assert "z-1" in result
        assert "z+1" in result
        assert "buy" in result
        assert "sell" in result
