from typing import Dict, Any, List, Union, Callable
import pandas as pd
import numpy as np
from ..registry.registry import IndicatorRegistry


class IndicatorCalculator:
    def __init__(self, registry: IndicatorRegistry):
        self._registry = registry
        self._cache: Dict[str, Union[np.ndarray, Dict[str, np.ndarray]]] = {}

    def calculate(
        self,
        name: str,
        candle_df: pd.DataFrame,
        **kwargs
    ) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        cache_key = self._generate_cache_key(name, candle_df, **kwargs)

        if cache_key in self._cache:
            return self._cache[cache_key]

        indicator_func = self._registry.get(name)
        result = indicator_func(candle_df, **kwargs)

        self._cache[cache_key] = result
        return result

    def calculate_batch(
        self,
        requests: List[Dict[str, Any]],
        candle_df: pd.DataFrame,
        clear_cache: bool = True
    ) -> Dict[str, Union[np.ndarray, Dict[str, np.ndarray]]]:
        if clear_cache:
            self.clear_cache()

        results = {}

        for req in requests:
            req_copy = req.copy()
            name = req_copy.pop("name")
            result_key = self._generate_result_key(name, **req_copy)

            result = self.calculate(name, candle_df, **req_copy)
            results[result_key] = result

        return results

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_cache_size(self) -> int:
        return len(self._cache)

    def _generate_cache_key(
        self,
        name: str,
        candle_df: pd.DataFrame,
        **kwargs
    ) -> str:
        df_id = id(candle_df)
        params_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{name}_{df_id}_{params_str}" if params_str else f"{name}_{df_id}"

    def _generate_result_key(self, name: str, **kwargs) -> str:
        params_str = "_".join(str(v) for v in kwargs.values())
        return f"{name}_{params_str}" if params_str else name
