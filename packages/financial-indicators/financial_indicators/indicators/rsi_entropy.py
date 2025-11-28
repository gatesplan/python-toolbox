import numpy as np
import pandas as pd
from typing import Dict
from .rsi import calculate_rsi
from ..core.rolling import sma, std
from ..registry import register


@register("rsi_entropy")
def calculate_rsi_entropy(
    candle_df: pd.DataFrame,
    rsi_period: int = 20,
    rsi_use: str = 'close',
    entropy_window: int = 365
) -> Dict[str, np.ndarray]:
    if len(candle_df) == 0:
        empty_array = np.array([])
        return {
            'base': empty_array,
            'z-1': empty_array,
            'z+1': empty_array,
            'buy': empty_array,
            'sell': empty_array
        }

    if rsi_use not in candle_df.columns:
        raise ValueError(f"DataFrame must contain '{rsi_use}' column")

    if rsi_period < 1:
        raise ValueError("rsi_period must be >= 1")

    if entropy_window < 2:
        raise ValueError("entropy_window must be >= 2")

    rsi_values = calculate_rsi(candle_df, period=rsi_period, use=rsi_use)
    rsi_scaled = rsi_values / 100.0

    rsi_mean = sma(rsi_scaled, window=entropy_window)
    rsi_std = std(rsi_scaled, window=entropy_window, ddof=0)

    rsi_z_minus = rsi_mean - rsi_std
    rsi_z_plus = rsi_mean + rsi_std

    buy_entropy, sell_entropy = _calculate_directional_entropy(
        rsi_scaled, rsi_mean, rsi_std
    )

    return {
        'base': rsi_scaled,
        'z-1': rsi_z_minus,
        'z+1': rsi_z_plus,
        'buy': buy_entropy,
        'sell': sell_entropy
    }


def _calculate_directional_entropy(
    rsi_values: np.ndarray,
    rsi_mean: np.ndarray,
    rsi_std: np.ndarray
) -> tuple:
    n = len(rsi_values)
    buy_entropy = np.zeros(n)
    sell_entropy = np.zeros(n)

    for i in range(n):
        rsi = rsi_values[i]
        mean = rsi_mean[i]
        std_val = rsi_std[i]

        if std_val < 1e-10:
            if rsi < mean:
                buy_entropy[i] = 0.0
                sell_entropy[i] = 1.0
            else:
                buy_entropy[i] = 1.0
                sell_entropy[i] = 0.0
            continue

        if rsi < mean:
            deviation = (mean - rsi) / (std_val + 1e-10)
            p = 1.0 / (1.0 + np.exp(-deviation))
            p = np.clip(p, 0.01, 0.99)
            buy_entropy[i] = -(p * np.log2(p) + (1-p) * np.log2(1-p))
            sell_entropy[i] = 1.0
        else:
            deviation = (rsi - mean) / (std_val + 1e-10)
            p = 1.0 / (1.0 + np.exp(-deviation))
            p = np.clip(p, 0.01, 0.99)
            sell_entropy[i] = -(p * np.log2(p) + (1-p) * np.log2(1-p))
            buy_entropy[i] = 1.0

    return buy_entropy, sell_entropy
