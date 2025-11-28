import numpy as np
from financial_indicators.core.rolling import sma, ema, zscore
from financial_indicators.core.series import pct_change, crossover


class TestIntegration:
    def test_golden_cross_strategy(self):
        prices = np.array([100.0, 102.0, 101.0, 103.0, 105.0, 107.0, 106.0, 108.0, 110.0, 109.0])
        short_ma = sma(prices, window=3)
        long_ma = sma(prices, window=5)
        signal = crossover(short_ma, long_ma)
        assert len(signal) == len(prices)

    def test_technical_workflow(self):
        prices = np.array([100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0])
        ma_3 = sma(prices, window=3)
        ema_3 = ema(prices, span=3)
        returns = pct_change(prices, periods=1)
        z = zscore(prices, window=5)
        assert len(ma_3) == len(prices)
        assert len(ema_3) == len(prices)
        assert len(returns) == len(prices)
        assert len(z) == len(prices)
