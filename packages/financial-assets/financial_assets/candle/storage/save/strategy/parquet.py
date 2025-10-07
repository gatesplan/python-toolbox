from pathlib import Path
import pandas as pd
from functools import reduce
from math import gcd
from .....stock_address import StockAddress
from .base import BaseSaveStrategy
from simple_logger import init_logging, func_logging


class ParquetSaveStrategy(BaseSaveStrategy):
    """Parquet 데이터 저장 전략"""

    @init_logging
    def __init__(self, config: dict):
        """
        Args:
            config: 환경변수 설정 dict (basepath 포함)
        """
        self.basepath = Path(config['basepath'])

    @func_logging
    def save(self, address: StockAddress, df: pd.DataFrame, storage_last_ts: int = None) -> None:
        """
        데이터 저장

        Args:
            address: StockAddress 객체
            df: 저장할 DataFrame
            storage_last_ts: 저장소에 기록된 마지막 타임스탬프
        """
        filepath = self.basepath / f"{address.to_filename()}.parquet"

        if storage_last_ts is None:
            # 초기 저장
            if filepath.exists():
                raise FileExistsError(f"File already exists: {filepath}")

            # round(4) 전처리
            df_to_save = self._preprocess(df.copy())

            # tick 변환 및 저장
            self._save_with_tick(df_to_save, filepath)
        else:
            # 업데이트 저장
            # 기존 파일 로드
            existing_df = pd.read_parquet(filepath)

            # metadata에서 unit 읽기
            metadata = pd.read_parquet(filepath).attrs
            unit = metadata.get('unit', 1)

            # tick을 timestamp로 역변환
            if 'tick' in existing_df.columns:
                existing_df['timestamp'] = existing_df['tick'] * unit
                existing_df = existing_df.drop(columns=['tick'])

            # storage_last_ts 이상 데이터 제거
            existing_df = existing_df[existing_df['timestamp'] < storage_last_ts]

            # df에서 storage_last_ts 이상만 필터링
            df_to_add = df[df['timestamp'] >= storage_last_ts].copy()

            # round(4) 전처리
            df_to_add = self._preprocess(df_to_add)

            # 병합
            combined_df = pd.concat([existing_df, df_to_add], ignore_index=True)
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

            # tick 변환 및 저장
            self._save_with_tick(combined_df, filepath)

    @func_logging
    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 전처리: HLOCV 값을 round(4)

        Args:
            df: DataFrame

        Returns:
            전처리된 DataFrame
        """
        df['high'] = df['high'].round(4)
        df['low'] = df['low'].round(4)
        df['open'] = df['open'].round(4)
        df['close'] = df['close'].round(4)
        return df

    @func_logging
    def _timestamp_to_tick(self, timestamps: pd.Series) -> tuple[pd.Series, int]:
        """
        타임스탬프를 tick으로 변환

        Args:
            timestamps: 타임스탬프 Series

        Returns:
            (ticks, unit)
        """
        # 단일 행인 경우 unit=1
        if len(timestamps) == 1:
            unit = 1
            ticks = timestamps.astype(int)
            return ticks, unit

        # diff 계산
        diffs = timestamps.diff().dropna()
        unique_diffs = diffs.unique()

        # 최대공약수 계산
        unit = reduce(gcd, unique_diffs.astype(int))

        # timestamp를 unit으로 나눈 몫을 tick으로 변환
        ticks = (timestamps // unit).astype(int)

        return ticks, unit

    @func_logging
    def _save_with_tick(self, df: pd.DataFrame, filepath: Path) -> None:
        """
        tick 변환 후 저장

        Args:
            df: 저장할 DataFrame
            filepath: 저장 경로
        """
        # timestamp를 tick으로 변환
        ticks, unit = self._timestamp_to_tick(df['timestamp'])

        # timestamp를 tick으로 교체
        df_to_save = df.copy()
        df_to_save['tick'] = ticks
        df_to_save = df_to_save.drop(columns=['timestamp'])

        # 컬럼 순서 재정렬: tick을 맨 앞으로
        cols = ['tick', 'high', 'low', 'open', 'close', 'volume']
        df_to_save = df_to_save[cols]

        # metadata에 unit 저장 (int로 변환하여 JSON serialization 문제 방지)
        df_to_save.attrs['unit'] = int(unit)

        # parquet 저장
        df_to_save.to_parquet(filepath, index=False)
