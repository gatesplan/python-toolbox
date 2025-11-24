"""TensorBuilder: List[Candle]을 3D numpy 텐서로 변환"""

import numpy as np
import pandas as pd
from typing import List
from simple_logger import func_logging


class TensorBuilder:
    """List[Candle] 객체들을 3D numpy 텐서로 변환하는 정적 유틸리티 클래스"""

    @staticmethod
    @func_logging(log_params=True)
    def build(candles: List) -> tuple[np.ndarray, list[str], np.ndarray]:
        """
        Candle 리스트를 3D 텐서로 변환

        Args:
            candles: Candle 객체 리스트

        Returns:
            tuple[np.ndarray, list[str], np.ndarray]:
                - tensor: (n_symbols, n_timestamps, 5) 3D array
                - symbols: 종목 리스트 (시작 시점 빠른 순 정렬)
                - timestamps: 타임스탬프 배열 (정렬됨)

        Raises:
            ValueError: candles가 비어있는 경우
            ValueError: candles의 exchange가 서로 다른 경우
        """
        # 빈 리스트 검증
        if len(candles) == 0:
            raise ValueError("candles가 비어있습니다")

        # exchange 일치 검증
        exchanges = {candle.address.exchange for candle in candles}
        if len(exchanges) > 1:
            raise ValueError(f"모든 candle은 같은 exchange여야 합니다. 발견된 exchange: {exchanges}")

        # 1. 타임스탬프 합집합 수집 (이미 정렬된 상태)
        all_timestamps = set()
        for candle in candles:
            if not candle.candle_df.empty:
                all_timestamps.update(candle.candle_df['timestamp'].values)

        timestamps = np.array(sorted(all_timestamps), dtype=np.int64)

        # 2. 종목 및 시작 시점 수집, 시작 시점 기준 정렬
        symbol_info = []
        for candle in candles:
            symbol = candle.address.to_symbol().to_slash()
            if not candle.candle_df.empty:
                first_ts = int(candle.candle_df['timestamp'].iloc[0])
            else:
                first_ts = np.inf  # 빈 데이터는 뒤로
            symbol_info.append((symbol, first_ts, candle))

        # 시작 시점 빠른 순 정렬
        symbol_info.sort(key=lambda x: x[1])
        symbols = [info[0] for info in symbol_info]

        # 3. 텐서 할당 (NaN 초기화)
        n_symbols = len(symbols)
        n_timestamps = len(timestamps)
        tensor = np.full((n_symbols, n_timestamps, 5), np.nan, dtype=np.float64)

        # 4. timestamp → index 매핑
        ts_to_idx = {int(ts): idx for idx, ts in enumerate(timestamps)}

        # 5. 각 Candle의 데이터를 텐서에 채우기
        for symbol_idx, (symbol, _, candle) in enumerate(symbol_info):
            if candle.candle_df.empty:
                continue

            df = candle.candle_df
            for _, row in df.iterrows():
                ts = int(row['timestamp'])
                ts_idx = ts_to_idx[ts]

                # OHLCV 순서로 배치
                tensor[symbol_idx, ts_idx, 0] = float(row['open'])
                tensor[symbol_idx, ts_idx, 1] = float(row['high'])
                tensor[symbol_idx, ts_idx, 2] = float(row['low'])
                tensor[symbol_idx, ts_idx, 3] = float(row['close'])
                tensor[symbol_idx, ts_idx, 4] = float(row['volume'])

        return tensor, symbols, timestamps
